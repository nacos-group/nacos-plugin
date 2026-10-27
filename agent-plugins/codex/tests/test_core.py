# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
import copy
import io
import json
from pathlib import Path
import stat
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import zipfile

from nacos_registry import package
from nacos_registry.errors import PluginError
from nacos_registry.hosts import codex
from nacos_registry.service import Service, governance
from nacos_registry.store import Store, digest
from nacos_registry.server import serve


def files(name="sample-skill", body="A harmless sample.", version="1.0.0"):
    return {"SKILL.md": f"---\nname: {name}\ndescription: Test sample.\nversion: {version}\n---\n\n{body}\n".encode()}


class FakeRegistry:
    def __init__(self):
        self.meta = None
        self.content = files()
        self.calls = []
        self.failure = None

    def search(self, **kwargs):
        self.calls.append(("search", kwargs))
        return {"items": [], "nextCursor": "opaque"}

    def skill_meta(self, name):
        if self.meta is None: raise PluginError("not_found", "Missing")
        return copy.deepcopy(self.meta)

    def precheck(self, data):
        self.calls.append(("precheck", data))
        return [{"skillName": package.metadata(package.unpack(data)["SKILL.md"])["name"], "precheckCode": "DRAFT_EXISTS" if self.meta and self.meta.get("editingVersion") else "READY", "editingVersion": self.meta.get("editingVersion") if self.meta else None, "targetVersion": "1.0.0"}]

    def draft_zip(self, name, version):
        return package.pack(self.content)

    def upload(self, data, action, version, message):
        self.calls.append(("upload", action))
        if self.failure: raise self.failure
        self.content = package.unpack(data)
        name = package.metadata(self.content["SKILL.md"])["name"]
        self.meta = {"name": name, "scope": "PRIVATE", "editingVersion": version, "versions": [{"version": version, "status": "draft"}]}
        return name

    def lifecycle(self, name, version, action):
        self.calls.append((action, version))
        if self.failure: raise self.failure
        self.meta["editingVersion"] = None
        self.meta["versions"][0]["status"] = "online"

    def download(self, name, version=None, label=None):
        self.calls.append(("download", version))
        if self.failure: raise self.failure
        return version or "1.0.0", "server-md5", package.pack(self.content)

    def discover(self, kind, name, version=None):
        return {"name": name, "version": "1.0.0", "protocol": "mcp-streamable", "frontendEndpoints": [{"protocol": "https", "address": "tools.example.org", "port": 443, "path": "/mcp"}]}


class PackageTests(unittest.TestCase):
    def test_roundtrip_and_unicode(self):
        value = files(); value["资料.txt"] = "资源".encode()
        self.assertEqual(value, package.unpack(package.pack(value)))

    def test_multiline_yaml_and_duplicate_keys(self):
        data = b"---\nname: sample\ndescription: >-\n  multi\n  line\n---\n"
        self.assertEqual(package.metadata(data)["description"], "multi line")
        with self.assertRaises(PluginError): package.metadata(data.replace(b"description:", b"name: other\ndescription:"))

    def test_alias_rejected(self):
        with self.assertRaises(PluginError): package.metadata(b"---\nname: sample\ndescription: &a hello\nextra: *a\n---\n")

    def archive(self, entries):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, content in entries: archive.writestr(name, content)
        return buffer.getvalue()

    def test_traversal_absolute_and_case_collisions(self):
        for name in ("../outside", "/absolute", "C:/windows", "dir\\file", "skill.md"):
            with self.subTest(name=name), self.assertRaises(PluginError):
                package.unpack(self.archive([("SKILL.md", files()["SKILL.md"]), (name, b"data")]))

    def test_symlinks_and_duplicates(self):
        info = zipfile.ZipInfo("link")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(PluginError): package.unpack(self.archive([("SKILL.md", files()["SKILL.md"]), (info, b"/secret")]))
        with self.assertRaises(PluginError): package.unpack(self.archive([("SKILL.md", files()["SKILL.md"]), ("SKILL.md", b"other")]))

    def test_missing_reference_and_script_not_executed(self):
        value = files(body="Read [manual](manual.md).")
        with self.assertRaises(PluginError): package.pack(value)
        value["manual.md"] = b"No execution."
        value["script.sh"] = b"exit 7"
        self.assertEqual(package.unpack(package.pack(value)), value)

    def test_directory_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root); (p/"SKILL.md").write_bytes(files()["SKILL.md"])
            (p/"escape").symlink_to("/tmp")
            with self.assertRaises(PluginError): package.read_directory(p)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root/"skills/sample-skill"
        self.source.mkdir(parents=True)
        (self.source/"SKILL.md").write_bytes(files()["SKILL.md"])
        self.remote = FakeRegistry()
        self.service = Service(Store(self.root/"state"), lambda _: self.remote)
        self.profile = {"id": "example", "identityId": "test-user", "namespaceId": "test", "clientUrl": "https://registry.example.org/nacos", "adminUrl": "https://registry.example.org/nacos", "allowedOperations": ["read", "develop", "publish", "install", "call"], "scanRoots": [str(self.source.parent)], "installRoots": [str(self.root/"host/.agents/skills")], "codexConfig": str(self.root/"host/.codex/config.toml")}
        self.call("configure", profile=self.profile)

    def tearDown(self): self.temp.cleanup()
    def call(self, method, **args): return self.service.invoke(method, args)
    def scan(self):
        scan = self.call("scan")
        return {"scanId": scan["id"], "candidateId": scan["items"][0]["id"]}
    def install(self):
        plan = self.call("install_plan", name="sample-skill", installRoot=self.profile["installRoots"][0])
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "completed")
        return result

    def test_scan_is_local_and_can_skip_reopen(self):
        candidate = self.scan()
        self.assertEqual(self.remote.calls, [])
        selected = self.call("select", scanId=candidate["scanId"], selections=[{"candidateId": candidate["candidateId"], "action": "track"}])
        self.assertEqual(selected["results"][0]["status"], "track")
        self.assertEqual(self.call("onboarding", action="skip")["status"], "skipped")
        self.assertEqual(self.call("onboarding", action="reopen")["status"], "awaiting_scan")
        self.assertEqual(self.remote.calls, [])

    def test_cancel_wrong_task_response_retains_unknown_outcome(self):
        with self.service.store.locked():
            context = digest(self.service.profile())
            connection = {"context": context, "ref": self.service.reference("agent", "sample-agent"),
                          "version": "1.0.0", "endpoint": {"url": "https://agent.example.org/rpc"}, "auth": {"type": "none"}}
            self.service.data["tasks"]["handle"] = {"taskId": "expected-task", "context": context, "connection": connection}
            self.service.store.save()
        for action, expected in (("get", "failed"), ("cancel", "result_unknown")):
            with self.subTest(action=action), patch('nacos_registry.remote.JsonRpc.request', return_value={"kind": "task", "id": "different-task"}) as request:
                result = self.call("agent_task", taskHandle="handle", action=action)
                self.assertEqual(result["status"], expected)
                self.assertEqual(self.call("inspect_operation", operationId=result["id"])["status"], expected)
                request.assert_called_once()

    def test_upload_draft_does_not_submit(self):
        plan = self.call("upload_plan", **self.scan())
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["result"]["status"], "draft")
        self.assertNotIn("submit", [x[0] for x in self.remote.calls])
        self.assertEqual(self.call("apply", planId=plan["id"]), result)
        self.assertEqual(sum(x[0] == "upload" for x in self.remote.calls), 1)

    def test_upload_modified_after_plan_blocked(self):
        plan = self.call("upload_plan", **self.scan())
        (self.source/"new.txt").write_text("changed")
        self.assertEqual(self.call("apply", planId=plan["id"])["error"]["error"], "conflict")
        self.assertNotIn("upload", [x[0] for x in self.remote.calls])

    def test_existing_draft_requires_binding_and_overwrite(self):
        plan = self.call("upload_plan", **self.scan()); self.call("apply", planId=plan["id"])
        with self.assertRaises(PluginError): self.call("upload_plan", **self.scan())
        next_plan = self.call("upload_plan", **self.scan(), overwriteDraft=True)
        self.assertEqual(next_plan["action"], "OVERWRITE_DRAFT")
        self.remote.content = files(body="Concurrent remote edit")
        result = self.call("apply", planId=next_plan["id"])
        self.assertEqual(result["error"]["error"], "conflict")

    def test_unknown_upload_never_blindly_retried(self):
        plan = self.call("upload_plan", **self.scan())
        self.remote.failure = PluginError("result_unknown", "Timed out")
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "result_unknown")
        with self.assertRaises(PluginError): self.call("apply", planId=plan["id"])

    def test_submit_can_go_online_and_exact_read_verified(self):
        plan = self.call("upload_plan", **self.scan()); self.call("apply", planId=plan["id"])
        plan = self.call("publish_plan", name="sample-skill", version="1.0.0", action="submit")
        self.assertEqual(plan["visibility"], "PRIVATE")
        result = self.call("apply", planId=plan["id"])["result"]
        self.assertEqual(result["status"], "online")
        self.assertTrue(result["consumerVerified"])

    def test_install_stale_plan_local_edits_and_uninstall(self):
        result = self.install(); item = result["result"]
        self.assertEqual(item["loadState"], "pending_host_verification")
        target = Path(item["target"])
        (target/"mine.txt").write_text("keep me")
        with self.assertRaises(PluginError): self.call("uninstall_plan", installationId=item["id"])
        with self.assertRaises(PluginError): self.call("install_plan", name="sample-skill", installRoot=self.profile["installRoots"][0])
        self.assertEqual((target/"mine.txt").read_text(), "keep me")

    def test_update_recovery_and_safe_uninstall(self):
        first = self.install()["result"]
        self.remote.content = files(body="Second version")
        second = self.install()
        self.remote.content = files()
        self.assertEqual(self.call("recover", operationId=second["id"])["status"], "recovered")
        self.assertEqual((Path(first["target"])/"SKILL.md").read_bytes(), files()["SKILL.md"])
        plan = self.call("uninstall_plan", installationId=first["id"])
        result = self.call("apply", planId=plan["id"])
        self.assertFalse(Path(first["target"]).exists())
        self.assertEqual(self.call("recover", operationId=result["id"])["status"], "recovered")
        self.assertTrue(Path(first["target"]).exists())

    def test_remote_permission_rechecked_before_install(self):
        plan = self.call("install_plan", name="sample-skill", installRoot=self.profile["installRoots"][0])
        self.remote.failure = PluginError("permission", "Revoked")
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["error"]["error"], "permission")
        self.assertFalse(Path(plan["target"]).exists())

    def test_context_change_invalidates_scan_and_plans(self):
        candidate = self.scan()
        self.call("configure", profile={**self.profile, "identityId": "another-user"})
        with self.assertRaises(PluginError): self.call("upload_plan", **candidate)

    def test_consumer_does_not_need_admin_but_cannot_upload(self):
        self.call("configure", profile={**self.profile, "allowedOperations": ["read", "install"]})
        self.call("search", query="test")
        with self.assertRaises(PluginError): self.call("upload_plan", **self.scan())

    def test_native_config_preserves_user_bytes_and_secrets(self):
        path = Path(self.profile["codexConfig"]); path.parent.mkdir(parents=True)
        original = b'# personal config\nmodel = "test"\n[mcp_servers.other]\nurl = "https://other.example.org/mcp"\nhttp_headers = { "Secret" = "DO-NOT-EXPOSE" }\n'
        path.write_bytes(original)
        plan = self.call("connection_plan", resourceType="mcp", name="tools")
        self.assertNotIn("DO-NOT-EXPOSE", json.dumps(plan))
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "completed")
        self.assertTrue(path.read_bytes().startswith(original))
        self.assertEqual(result["result"]["status"], "pending_host_reload")

    def test_native_name_is_readable_bounded_and_scope_specific(self):
        plan = self.call("connection_plan", resourceType="mcp", name="team-tools")
        key = plan["configKey"]
        self.assertRegex(key, r"^nacos_team-tools_[a-f0-9]{12}$")
        self.assertEqual(tomllib.loads(plan["configBlock"])["mcp_servers"][key]["url"], plan["endpoint"]["url"])
        self.call("configure", profile={**self.profile, "namespaceId": "other"})
        other = self.call("connection_plan", resourceType="mcp", name="team-tools")
        self.assertNotEqual(key, other["configKey"])
        for name in ('Mixed Case.Service', '工具服务', 'x' * 500, 'a\"]\n[other]'):
            with self.subTest(name=name):
                value = codex.connection_key(name, plan["connectionId"])
                self.assertLessEqual(len(value), 51)
                self.assertRegex(value, r"^nacos_[a-z0-9_-]+_[a-f0-9]{12}$")
                parsed = tomllib.loads(codex.connection_block(value, "https://tools.example.org/mcp", {"type": "none"}))
                self.assertEqual(list(parsed), ["mcp_servers"])
                self.assertEqual(list(parsed["mcp_servers"]), [value])

    def legacy_mcp(self):
        with patch.object(codex, "connection_key", side_effect=lambda name, ident: "nacos_" + ident[:20]):
            plan = self.call("connection_plan", resourceType="mcp", name="team-tools")
        return self.call("apply", planId=plan["id"])["result"]

    def test_legacy_native_rename_preserves_bytes_recovers_and_reuses(self):
        path = Path(self.profile["codexConfig"]); path.parent.mkdir(parents=True)
        original = b'# user settings\n[mcp_servers.personal]\nurl = "https://personal.example.org/mcp"\n'
        path.write_bytes(original)
        old = self.legacy_mcp()
        before = path.read_bytes()
        plan = self.call("connection_plan", resourceType="mcp", name="team-tools")
        self.assertIn(old["configKey"], " ".join(plan["effects"]))
        self.assertEqual(path.read_bytes(), before)  # Planning must not rename.
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "completed")
        new = result["result"]
        self.assertEqual(new["id"], old["id"])
        self.assertEqual(set(tomllib.loads(path.read_text())["mcp_servers"]), {"personal", new["configKey"]})
        self.assertTrue(path.read_bytes().startswith(original))
        self.assertEqual(self.call("recover", operationId=result["id"])["status"], "recovered")
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.service.data["connections"][old["id"]]["configKey"], old["configKey"])
        for _ in range(2):
            plan = self.call("connection_plan", resourceType="mcp", name="team-tools")
            self.assertEqual(self.call("apply", planId=plan["id"])["status"], "completed")
        self.assertEqual(set(tomllib.loads(path.read_text())["mcp_servers"]), {"personal", new["configKey"]})
        removal = self.call("disconnect_plan", connectionId=new["id"])
        self.call("apply", planId=removal["id"])
        self.assertEqual(path.read_bytes(), original)

    def test_legacy_native_rename_refuses_edits_and_name_collision(self):
        old = self.legacy_mcp(); path = Path(old["configPath"])
        baseline = path.read_bytes()
        new_key = codex.connection_key("team-tools", old["id"])
        variants = [baseline.replace(b'url = ', b'enabled = false\nurl = '),
                    baseline + f'\n[mcp_servers.{new_key}]\nurl = "https://user.example.org/mcp"\n'.encode()]
        for content in variants:
            with self.subTest(content=content):
                path.write_bytes(content)
                with self.assertRaises(PluginError) as error:
                    self.call("connection_plan", resourceType="mcp", name="team-tools")
                self.assertEqual(error.exception.kind, "conflict")
                self.assertEqual(path.read_bytes(), content)
                self.assertEqual(self.service.data["connections"][old["id"]], old)

    def test_legacy_native_rename_rechecks_configuration_before_apply(self):
        old = self.legacy_mcp(); path = Path(old["configPath"])
        plan = self.call("connection_plan", resourceType="mcp", name="team-tools")
        edited = path.read_bytes() + b'\n# later user edit\n'; path.write_bytes(edited)
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["error"]["error"], "conflict")
        self.assertEqual(path.read_bytes(), edited)
        self.assertEqual(self.service.data["connections"][old["id"]], old)

    def test_mcp_probe_reports_native_loading_separately_without_executing_tools(self):
        plan = self.call("connection_plan", resourceType="mcp", name="tools")
        connection = self.call("apply", planId=plan["id"])["result"]
        config = Path(connection["configPath"]).read_bytes()
        tool = {"name": "find_items", "inputSchema": {"type": "object", "properties": {}}}
        # Neither a genuine tool catalog nor untrusted extra fields prove host loading/use.
        for extra in ({}, {"hostLoaded": "verified", "realUse": "verified",
                           "nativeServerName": "another_server", "loadingHint": "already loaded"}):
            with self.subTest(extra=extra), patch("nacos_registry.remote.JsonRpc") as client:
                rpc = client.return_value
                rpc.initialize_mcp.return_value = {"capabilities": {"tools": {}}}
                rpc.request.return_value = {"tools": [tool], **extra}
                result = self.call("mcp_probe", connectionId=connection["id"])
                rpc.initialize_mcp.assert_called_once_with()
                rpc.request.assert_called_once_with("tools/list", {})
                rpc.close_mcp.assert_called_once_with()
            self.assertEqual(result["tools"], [tool])
            self.assertEqual(result["transport"], "connected")
            self.assertEqual(result["nativeServerName"], connection["configKey"])
            self.assertEqual(result["hostLoaded"], "unverified")
            self.assertEqual(result["realUse"], "unverified")
            self.assertIn("Restart", result["loadingHint"])
            self.assertEqual(Path(connection["configPath"]).read_bytes(), config)
            stored = self.service.data["connections"][connection["id"]]
            self.assertEqual(stored["status"], "pending_host_reload")
            self.assertEqual(stored["probeStatus"], "tools_discovered")

    def test_mcp_probe_failure_does_not_mark_tools_discovered(self):
        plan = self.call("connection_plan", resourceType="mcp", name="tools")
        connection = self.call("apply", planId=plan["id"])["result"]
        with patch("nacos_registry.remote.JsonRpc") as client:
            rpc = client.return_value
            rpc.initialize_mcp.return_value = {"capabilities": {"tools": {}}}
            rpc.request.side_effect = PluginError("connection", "Unavailable")
            with self.assertRaises(PluginError):
                self.call("mcp_probe", connectionId=connection["id"])
            rpc.close_mcp.assert_called_once_with()
        stored = self.service.data["connections"][connection["id"]]
        self.assertEqual(stored["status"], "pending_host_reload")
        self.assertNotIn("probeStatus", stored)

    def test_reconcile_lost_upload_response_without_replay(self):
        plan = self.call("upload_plan", **self.scan())
        original = self.remote.upload
        def lose_response(*args):
            original(*args)
            raise PluginError("result_unknown", "Response lost after server accepted draft")
        self.remote.upload = lose_response
        operation = self.call("apply", planId=plan["id"])
        self.assertEqual(operation["status"], "result_unknown")
        result = self.call("reconcile", operationId=operation["id"])
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["reconciled"])
        self.assertEqual(sum(x[0] == "upload" for x in self.remote.calls), 1)

    def test_newer_remote_publication_blocks_local_upload(self):
        plan = self.call("upload_plan", **self.scan()); self.call("apply", planId=plan["id"])
        self.remote.meta["labels"] = {"latest": "9.0.0"}
        with self.assertRaises(PluginError) as caught:
            self.call("upload_plan", **self.scan(), overwriteDraft=True)
        self.assertEqual(caught.exception.kind, "conflict")

    def test_connection_disconnect_recover_and_modified_block(self):
        plan = self.call("connection_plan", resourceType="mcp", name="tools")
        applied = self.call("apply", planId=plan["id"])
        connection = applied["result"]
        removal = self.call("disconnect_plan", connectionId=connection["id"])
        removed = self.call("apply", planId=removal["id"])
        self.assertNotIn("mcp_servers", Path(connection["configPath"]).read_text())
        self.assertEqual(self.call("recover", operationId=removed["id"])["status"], "recovered")
        path = Path(connection["configPath"])
        path.write_text(path.read_text().replace('url = ', 'enabled = false\nurl = '))
        with self.assertRaises(PluginError): self.call("disconnect_plan", connectionId=connection["id"])
        self.assertIn("enabled = false", path.read_text())

    def test_restore_after_profile_switch_retains_plan(self):
        item = self.install()
        self.call("configure", profile={**self.profile, "identityId": "another-user"})
        with self.assertRaises(PluginError): self.call("recover", operationId=item["id"])
        self.call("configure", profile=self.profile)
        self.assertEqual(self.call("recover", operationId=item["id"])["status"], "recovered")

    def test_batch_selection_reports_partial_failure(self):
        candidate = self.scan()
        result = self.call("select", scanId=candidate["scanId"], selections=[{"candidateId": candidate["candidateId"], "action": "ignore"}, {"candidateId": "missing", "action": "track"}])
        self.assertEqual(result["results"][0]["status"], "ignore")
        self.assertIn("error", result["results"][1])
        self.assertEqual(self.remote.calls, [])

    def test_review_rejection_never_force_publishes(self):
        plan = self.call("upload_plan", **self.scan()); self.call("apply", planId=plan["id"])
        self.remote.meta["versions"][0].update(status="reviewed", publishPipelineInfo=json.dumps({"status": "REJECTED"}))
        with self.assertRaises(PluginError) as caught:
            self.call("publish_plan", name="sample-skill", version="1.0.0", action="publish")
        self.assertEqual(caught.exception.kind, "review_rejected")
        self.assertNotIn("force-publish", [x[0] for x in self.remote.calls])
        self.assertNotIn("publish", [x[0] for x in self.remote.calls])

    def test_failure_between_renames_can_restore_previous_snapshot(self):
        from unittest.mock import patch
        import os
        first = self.install()["result"]
        self.remote.content = files(body="Replacement")
        plan = self.call("install_plan", name="sample-skill", installRoot=self.profile["installRoots"][0])
        original = os.rename
        calls = 0
        def fail_second(source, target):
            nonlocal calls
            calls += 1
            if calls == 2: raise OSError("Injected interruption")
            return original(source, target)
        with patch("nacos_registry.service.os.rename", side_effect=fail_second):
            failed = self.call("apply", planId=plan["id"])
        self.assertEqual(failed["status"], "recovery_required")
        self.remote.content = files()
        self.assertEqual(self.call("recover", operationId=failed["id"])["status"], "recovered")
        self.assertEqual((Path(first["target"])/"SKILL.md").read_bytes(), files()["SKILL.md"])

    def test_mcp_discovery_guidance_needs_no_configuration_or_registry_access(self):
        state_before = self.service.store.file.read_bytes()
        unconfigured = Service(Store(self.root / "unconfigured"), lambda _: self.remote)
        instructions = set()
        for service in (self.service, unconfigured):
            for version in ("2024-11-05", "2025-03-26", "2025-06-18"):
                with self.subTest(configured=service is self.service, version=version):
                    request = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                               "params": {"protocolVersion": version}}
                    output = io.StringIO()
                    with patch.object(service, "invoke", side_effect=AssertionError("Initialization must not invoke operations")):
                        serve(service, io.StringIO(json.dumps(request) + "\n"), output)
                    result = json.loads(output.getvalue())["result"]
                    self.assertEqual(result["protocolVersion"], version)
                    self.assertIsInstance(result["instructions"], str)
                    self.assertTrue(result["instructions"].strip())
                    instructions.add(result["instructions"])
                    for private_value in (self.profile["clientUrl"], self.profile["identityId"], str(self.root)):
                        self.assertNotIn(private_value, result["instructions"])
        self.assertEqual(len(instructions), 1)
        self.assertEqual(self.remote.calls, [])
        self.assertEqual(self.service.store.file.read_bytes(), state_before)
        self.assertFalse(unconfigured.store.file.exists())

    def test_mcp_wire_and_validation(self):
        requests = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "nacos_status", "arguments": {}}},
                    {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "nacos_scan", "arguments": {"unexpected": True}}}]
        output = io.StringIO()
        serve(self.service, io.StringIO("\n".join(json.dumps({"jsonrpc": "2.0", **x}) for x in requests)), output)
        values = [json.loads(x) for x in output.getvalue().splitlines()]
        self.assertGreater(len(values[1]["result"]["tools"]), 15)
        self.assertFalse(values[2]["result"]["isError"])
        self.assertTrue(values[3]["result"]["isError"])

    def test_page_context_change_rejects_write_and_clears_scan(self):
        self.scan()
        old = self.call("status")
        self.assertIsNotNone(old["scan"])
        self.call("configure", profile={**self.profile, "identityId": "other"})
        with self.assertRaises(PluginError) as caught:
            self.service.invoke("configure", {"profile": self.profile}, expected_context=old["context"])
        self.assertEqual(caught.exception.kind, "conflict")
        self.assertEqual(self.call("status")["profile"]["identityId"], "other")
        self.assertIsNone(self.call("status")["scan"])

    def test_upload_preview_does_not_transfer_and_changed_content_blocks_precheck(self):
        args = self.scan()
        preview = self.call("upload_preview", **args)
        self.assertEqual(preview["files"][0]["path"], "SKILL.md")
        self.assertEqual(self.remote.calls, [])
        (self.source/"new.txt").write_text("not in authorized file list")
        with self.assertRaises(PluginError):
            self.call("upload_plan", **args, expectedContentHash=preview["contentHash"])
        self.assertNotIn("precheck", [x[0] for x in self.remote.calls])

    def test_ui_resource_and_structured_results_share_core(self):
        from nacos_registry.server import UI_URI
        requests = [
            {"id": 1, "method": "initialize", "params": {}},
            {"id": 2, "method": "tools/list"},
            {"id": 3, "method": "resources/read", "params": {"uri": UI_URI}},
            {"id": 4, "method": "tools/call", "params": {"name": "nacos_status", "arguments": {}}},
            {"id": 5, "method": "tools/call", "params": {"name": "nacos_scan", "arguments": {"_context": "stale"}}},
        ]
        output = io.StringIO()
        serve(self.service, io.StringIO("\n".join(json.dumps({"jsonrpc": "2.0", **x}) for x in requests)), output)
        values = [json.loads(x)["result"] for x in output.getvalue().splitlines()]
        entries = [t for t in values[1]["tools"] if "resourceUri" in t["_meta"]["ui"]]
        self.assertEqual(len(entries), 2)
        self.assertEqual({t["_meta"]["openai/ui"]["entrypoints"][0]["type"] for t in entries}, {"thread", "global"})
        resource = values[2]["contents"][0]
        self.assertEqual(resource["mimeType"], "text/html;profile=mcp-app")
        self.assertIn("Nacos 资源中心", resource["text"])
        self.assertEqual(values[3]["structuredContent"], self.call("status"))
        self.assertTrue(values[4]["isError"])
        self.assertEqual(json.loads(values[4]["content"][0]["text"])["error"], "conflict")


if __name__ == "__main__": unittest.main()
