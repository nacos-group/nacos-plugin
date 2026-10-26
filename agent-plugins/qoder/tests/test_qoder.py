# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
import copy
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from nacos_registry import __version__ as registry_version, package
from nacos_registry.errors import PluginError
from nacos_registry.registry import Registry
from nacos_registry.schema import validate
from nacos_registry.store import Store, digest
from nacos_qoder import __version__
from nacos_qoder.host import local_defaults
from nacos_qoder.server import DEFINITIONS, call_tool, serve, tools_list
from nacos_qoder.service import Service


def skill(body="Harmless sample."):
    return {"SKILL.md": ("---\nname: sample-skill\ndescription: A harmless test skill.\nversion: 1.0.0\n---\n\n" + body + "\n").encode()}


class FakeRegistry:
    def __init__(self):
        self.content = skill()
        self.meta = None
        self.calls = []
        self.endpoint = "tools.example.org"

    def search(self, **kwargs):
        self.calls.append("search")
        return {"items": [], "nextCursor": "opaque"}

    def download(self, name, version=None, label=None):
        self.calls.append("download")
        return version or "1.0.0", "server-md5", package.pack(self.content)

    def discover(self, kind, name, version=None):
        if kind == "agent":
            return {"name": name, "version": "1.0.0", "callInterfaces": [{
                "protocol": "a2a", "protocolVersion": "0.3.0",
                "nativeDescriptor": {"protocolVersion": "0.3.0", "preferredTransport": "JSONRPC"},
                "endpointSets": [{"source": "static", "endpoints": [{
                    "transport": "JSONRPC", "uri": "https://" + self.endpoint + "/rpc"}]}]}]}
        return {"name": name, "version": "1.0.0", "protocol": "mcp-streamable",
                "frontendEndpoints": [{"protocol": "https", "address": self.endpoint, "port": 443, "path": "/mcp"}]}

    def skill_meta(self, name):
        if self.meta is None:
            raise PluginError("not_found", "Missing")
        return copy.deepcopy(self.meta)

    def draft_zip(self, name, version):
        return package.pack(self.content)

    def precheck(self, data):
        self.calls.append("precheck")
        return [{"skillName": "sample-skill", "precheckCode": "READY", "targetVersion": "1.0.0"}]

    def upload(self, data, action, version, message):
        self.calls.append("upload")
        self.content = package.unpack(data)
        self.meta = {"name": "sample-skill", "scope": "PRIVATE", "editingVersion": version,
                     "versions": [{"version": version, "status": "draft"}]}
        return "sample-skill"

    def lifecycle(self, name, version, action):
        self.calls.append(action)
        self.meta["editingVersion"] = None
        self.meta["versions"][0]["status"] = "online"


class FakeVault:
    """In-memory Keychain stand-in; unit tests never touch the real login Keychain."""
    def __init__(self, root=None):
        self.entries, self.available, self.fail = {}, True, {}

    def capabilities(self):
        return {"available": self.available, "backend": "macos-keychain" if self.available else None,
                "reason": None if self.available else "secure_store_unavailable"}

    def check(self, action):
        if not self.available:
            raise PluginError("secure_store_unavailable", "Unavailable")
        if action in self.fail:
            raise PluginError(self.fail[action], "Synthetic Keychain failure")

    def put(self, ref, payload):
        self.check("put")
        self.entries[ref] = copy.deepcopy(payload)

    def get(self, ref):
        self.check("get")
        if ref not in self.entries:
            raise PluginError("credential_missing", "Missing")
        return copy.deepcopy(self.entries[ref])

    def delete(self, ref):
        self.check("delete")
        self.entries.pop(ref, None)


class FakePrompt:
    def __init__(self):
        self.answers, self.calls, self.available = [], [], True

    def capabilities(self):
        return {"available": self.available, "backend": "macos-dialog" if self.available else None,
                "reason": None if self.available else "secure_input_unavailable"}

    def collect(self, kind, label, url):
        self.calls.append((kind, label, url))
        answer = self.answers.pop(0)
        if callable(answer):
            answer = answer()
        if isinstance(answer, PluginError):
            raise answer
        return answer


class QoderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.enterContext(patch.dict("os.environ", {"HOME": str(self.root / "home")}, clear=True))
        self.enterContext(patch("nacos_qoder.host.Path.home", return_value=self.root / "home"))
        self.enterContext(patch("nacos_qoder.host.socket.gethostname", return_value="synthetic-host"))
        self.enterContext(patch("nacos_qoder.host.getpass.getuser", return_value="synthetic-user"))
        self.enterContext(patch("nacos_registry.registry.http", side_effect=AssertionError("Unexpected registry HTTP")))
        self.enterContext(patch("nacos_registry.downstream.http", side_effect=AssertionError("Unexpected downstream HTTP")))
        self.enterContext(patch("nacos_registry.service.Keychain", FakeVault))
        self.enterContext(patch("nacos_registry.service.NativePrompt", FakePrompt))
        self.source = self.root / "source/sample-skill"
        self.source.mkdir(parents=True)
        (self.source / "SKILL.md").write_bytes(skill()["SKILL.md"])
        self.remote = FakeRegistry()
        self.service = Service(Store(self.root / "state"), lambda *_: self.remote)
        self.profile = {"id": "test", "identityId": "test-user", "namespaceId": "test",
                        "clientUrl": "https://registry.example.org/nacos", "adminUrl": "https://registry.example.org/nacos",
                        "allowedOperations": ["read", "install", "develop", "publish", "call"],
                        "scanRoots": [str(self.source.parent)], "installRoots": [str(self.root / "host/.qoder/skills")]}
        self.call("configure", profile=self.profile)

    def call(self, method, **args):
        if method == "configure" and "expectedRevision" not in args:
            args["expectedRevision"] = self.service.invoke("status")["configurationRevision"]
        return self.service.invoke(method, args)

    def fresh_service(self, name="fresh", registry_factory=None):
        return Service(Store(self.root / name), registry_factory or (lambda *_: self.remote))

    def login_auth(self):
        return {"type": "login", "usernameEnv": "SYNTHETIC_USER", "passwordEnv": "SYNTHETIC_PASSWORD"}

    def configure_login(self):
        return self.call("configure", profile={"namespaceId": "test", "clientUrl": self.profile["clientUrl"],
                                              "allowedOperations": self.profile["allowedOperations"],
                                              "adminMode": "shared", "clientAuth": self.login_auth()})

    def upload_args(self):
        scan = self.call("scan")
        item = next(item for item in scan["items"] if item.get("status") == "candidate")
        return {"scanId": scan["id"], "candidateId": item["id"]}

    def upload_draft(self):
        args = self.upload_args()
        preview = self.call("upload_preview", **args)
        plan = self.call("upload_plan", **args, expectedContentHash=preview["contentHash"])
        return plan, self.call("apply", planId=plan["id"])

    def assert_rejected_without_save(self, action, arguments, kind="conflict", service=None):
        service = service or self.service
        before = service.store.file.read_bytes()
        with self.assertRaises(PluginError) as caught:
            service.invoke(action, arguments)
        self.assertEqual(caught.exception.kind, kind)
        self.assertEqual(service.store.file.read_bytes(), before)

    def install(self):
        plan = self.call("install_plan", name="sample-skill", installRoot=self.profile["installRoots"][0])
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "completed")
        return result

    def bind(self, kind="mcp", **kwargs):
        plan = self.call("connection_plan", resourceType=kind, name="test-" + kind, **kwargs)
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "completed")
        return result["result"]

    def test_defaults_only_qoder_personal_root_without_writes(self):
        with patch("nacos_qoder.host.Path.home", return_value=self.root / "home"):
            result = local_defaults(self.service.allowed_root)
            self.assertEqual(result["installRoots"], [str(self.root / "home/.qoder/skills")])
            self.assertEqual(result["scanRoots"], [])
            self.assertNotIn("codexConfig", result)
            self.assertFalse((self.root / "home").exists())
            (self.root / "home/.qoder/skills").mkdir(parents=True)
            self.assertEqual(local_defaults(self.service.allowed_root)["scanRoots"], result["installRoots"])

    def test_unsafe_defaults_have_no_fallback_to_other_host(self):
        (self.root / "home/.qoder").mkdir(parents=True)
        (self.root / "home/.qoder/skills").symlink_to(self.source.parent)
        with patch("nacos_qoder.host.Path.home", return_value=self.root / "home"):
            result = local_defaults(self.service.allowed_root)
        self.assertEqual(result["installRoots"], [])
        self.assertIn("defaultSkillsUnavailable", result["warnings"])

    def test_default_state_isolated_from_codex_environment(self):
        with patch.dict("os.environ", {"NACOS_PLUGIN_HOME": str(self.root / "codex")}, clear=True), \
                patch("nacos_registry.store.Path.home", return_value=self.root):
            service = Service()
        self.assertEqual(service.store.root, self.root / ".qoder/state/nacos-ai-registry")
        self.assertFalse((self.root / "codex").exists())

    def test_explicit_qoder_state_environment(self):
        with patch.dict("os.environ", {"NACOS_QODER_HOME": str(self.root / "qoder-state")}):
            self.assertEqual(Service().store.root, self.root / "qoder-state")

    def test_status_reports_unsupported_ui_and_does_not_scan(self):
        result = self.call("status")
        self.assertEqual(result["host"]["name"], "Qoder")
        self.assertEqual(result["host"]["pageCredentials"], "not_supported")
        self.assertEqual(result["credentialStorage"], {"available": True, "backend": "macos-keychain", "input": "macos-dialog",
                                                       "recommendedSource": "keychain", "fallbackSource": "environment",
                                                       "restartRequired": False, "reason": None})
        self.assertEqual(result["host"]["systemCredentialStore"], "macos_keychain")
        self.service.vault.available = False
        result = self.call("status")
        self.assertFalse(result["credentialStorage"]["available"])
        self.assertIsNone(result["credentialStorage"]["recommendedSource"])
        self.assertEqual(result["credentialStorage"]["reason"], "secure_store_unavailable")
        self.assertEqual(self.remote.calls, [])
        self.assertNotIn("codexConfig", result["defaults"])

    def test_codex_and_plaintext_or_page_auth_are_rejected(self):
        for field, value in (("codexConfig", str(self.root / "config.toml")),
                             ("clientAuth", {"type": "token", "token": "forbidden"}),
                             ("clientAuth", {"type": "login", "source": "local"}),
                             ("adminAuth", {"type": "none", "credentialRef": "a" * 32})):
            with self.subTest(field=field, value=value), self.assertRaises(PluginError):
                self.call("configure", profile={**self.profile, field: value})

    def test_schema_excludes_other_host_and_private_page_tools(self):
        profile = DEFINITIONS["configure"][1]["properties"]["profile"]["properties"]
        self.assertNotIn("codexConfig", profile)
        for field in ("clientAuth", "adminAuth"):
            self.assertEqual(profile[field]["properties"]["source"]["enum"], ["keychain", "environment"])
            self.assertNotIn("credentialRef", profile[field]["properties"])
        names = {item["name"] for item in tools_list()}
        self.assertIn("nacos_status", names)
        self.assertIn("nacos_credentials", names)
        self.assertNotIn("nacos_credentials_save", names)
        self.assertNotIn("nacos_open_center", names)
        for item in tools_list():
            self.assertNotIn("Codex", item["description"])
            self.assertNotIn("_meta", item)

    def test_protocol_source_and_version_are_local_to_qoder(self):
        source = Path(__file__).resolve().parents[1] / "src"
        self.assertTrue(Path(package.__file__).resolve().is_relative_to(source))
        self.assertEqual(registry_version, __version__)

    def test_scan_and_selection_never_upload(self):
        scan = self.call("scan")
        self.call("select", scanId=scan["id"], selections=[{"candidateId": scan["items"][0]["id"], "action": "track"}])
        self.assertEqual(self.remote.calls, [])
        self.assertEqual(self.call("onboarding", action="skip")["status"], "skipped")

    def test_onboarding_state_requires_current_scan_complete_choices_and_context(self):
        self.assertIn("_context", DEFINITIONS["onboarding"][1]["required"])
        unconfigured = self.fresh_service("unconfigured")
        with self.assertRaises(PluginError) as caught:
            unconfigured.invoke("onboarding", {"action": "skip"})
        self.assertEqual(caught.exception.kind, "configuration")
        self.assertFalse(unconfigured.store.file.exists())

        self.assert_rejected_without_save("onboarding", {"action": "finish"})
        self.assert_rejected_without_save("onboarding", {"action": "reopen"})
        previous = self.call("scan")
        self.assert_rejected_without_save("onboarding", {"action": "finish"})
        current = self.call("scan")
        self.assert_rejected_without_save("select", {"scanId": previous["id"], "selections": [
            {"candidateId": previous["items"][0]["id"], "action": "ignore"}]})
        self.call("select", scanId=current["id"], selections=[
            {"candidateId": current["items"][0]["id"], "action": "track"}])
        complete = self.call("onboarding", action="finish")
        self.assertEqual(complete, {"status": "complete", "scanId": current["id"]})
        self.assert_rejected_without_save("onboarding", {"action": "skip"})
        self.assertEqual(self.call("onboarding", action="reopen"), {"status": "awaiting_scan"})
        self.assertEqual(self.call("onboarding", action="skip"), {"status": "skipped"})
        self.assertIsNone(self.call("status")["scan"])
        self.assertEqual(self.remote.calls, [])

    def test_skill_upload_draft_then_explicit_publication(self):
        scan = self.call("scan")
        args = {"scanId": scan["id"], "candidateId": scan["items"][0]["id"]}
        preview = self.call("upload_preview", **args)
        plan = self.call("upload_plan", **args, expectedContentHash=preview["contentHash"])
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["result"]["status"], "draft")
        self.assertNotIn("submit", self.remote.calls)
        publish = self.call("publish_plan", name="sample-skill", version="1.0.0", action="submit")
        result = self.call("apply", planId=publish["id"])
        self.assertEqual(result["result"]["status"], "online")
        self.assertTrue(result["result"]["consumerVerified"])

    def test_skill_install_update_recover_and_uninstall(self):
        first = self.install()["result"]
        self.assertIn(".qoder/skills", first["target"])
        self.assertEqual(first["loadState"], "pending_host_verification")
        verify = self.call("verify_skill", installationId=first["id"])
        self.assertIn("Qoder", verify["next"])
        self.remote.content = skill("Updated.")
        second = self.install()
        self.remote.content = skill()
        self.assertEqual(self.call("recover", operationId=second["id"])["status"], "recovered")
        self.assertEqual((Path(first["target"]) / "SKILL.md").read_bytes(), skill()["SKILL.md"])
        plan = self.call("uninstall_plan", installationId=first["id"])
        self.assertEqual(self.call("apply", planId=plan["id"])["status"], "completed")
        self.assertFalse(Path(first["target"]).exists())

    def test_skill_conflict_preserves_local_content(self):
        first = self.install()["result"]
        path = Path(first["target"]) / "SKILL.md"
        path.write_bytes(skill("Local edit.")["SKILL.md"])
        with self.assertRaises(PluginError):
            self.install()
        self.assertIn(b"Local edit", path.read_bytes())

    def test_mcp_binding_is_not_native_configuration_write(self):
        item = self.bind()
        self.assertEqual(item["status"], "pending_host_registration")
        self.assertEqual(item["hostRegistration"]["config"], {"type": "http", "url": "https://tools.example.org:443/mcp"})
        self.assertNotIn("configPath", item)
        self.assertFalse((self.root / "host/.qoder/settings.json").exists())
        plan = self.call("disconnect_plan", connectionId=item["id"])
        self.assertEqual(plan["hostRemoval"], item["hostRegistration"])
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["result"]["hostState"], "pending_native_removal")
        self.assertEqual(self.call("status")["connections"], [])

    def test_mcp_bearer_reference_remains_nonsecret_and_requires_native_auth(self):
        item = self.bind(auth={"type": "bearer", "tokenEnv": "NACOS_PLUGIN_MCP_TOKEN"})
        self.assertEqual(item["hostRegistration"]["status"], "requires_native_authentication")
        self.assertNotIn("headers", item["hostRegistration"]["config"])
        self.assertNotIn("env", item["hostRegistration"]["config"])

    def test_registry_credentials_cannot_be_reused_for_mcp(self):
        profile = {**self.profile, "clientAuth": {"type": "token", "tokenEnv": "NACOS_PLUGIN_CLIENT_TOKEN"}}
        self.call("configure", profile=profile)
        with self.assertRaises(PluginError):
            self.bind(auth={"type": "bearer", "tokenEnv": "NACOS_PLUGIN_CLIENT_TOKEN"})

    def test_endpoint_changed_before_apply_keeps_binding_unmodified(self):
        plan = self.call("connection_plan", resourceType="mcp", name="test-mcp")
        self.remote.endpoint = "changed.example.org"
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error"], "conflict")
        self.assertEqual(self.call("status")["connections"], [])

    def test_changed_context_rejects_tool_and_plan(self):
        before = self.call("status")["context"]
        plan = self.call("connection_plan", resourceType="mcp", name="test-mcp")
        self.call("configure", profile={**self.profile, "namespaceId": "other"})
        with self.assertRaises(PluginError):
            self.service.invoke("status", expected_context=before)
        with self.assertRaises(PluginError):
            self.call("apply", planId=plan["id"])

    def test_mcp_probe_does_not_claim_host_loading(self):
        item = self.bind()
        with patch("nacos_registry.remote.JsonRpc") as rpc:
            rpc.return_value.initialize_mcp.return_value = {"capabilities": {"tools": {}}}
            rpc.return_value.request.return_value = {"tools": []}
            result = self.call("mcp_probe", connectionId=item["id"])
        self.assertEqual(result["hostLoaded"], "unverified")
        self.assertEqual(result["realUse"], "unverified")
        self.assertEqual(self.call("status")["connections"][0]["status"], "pending_host_registration")

    def test_a2a_send_query_cancel_stays_bound_to_original_endpoint(self):
        item = self.bind("agent")
        with patch("nacos_registry.remote.JsonRpc") as rpc:
            rpc.return_value.request.return_value = {"kind": "task", "id": "remote-task", "status": {"state": "working"}}
            sent = self.call("agent_send", connectionId=item["id"], text="Synthetic test input")
            handle = sent["taskHandle"]
            self.remote.endpoint = "new.example.org"
            self.call("agent_task", taskHandle=handle, action="get")
            rpc.return_value.request.return_value = {"kind": "task", "id": "remote-task", "status": {"state": "canceled"}}
            result = self.call("agent_task", taskHandle=handle, action="cancel")
            self.assertEqual(result["result"]["status"]["state"], "canceled")
            self.assertTrue(all(call.args[0] == "https://tools.example.org/rpc" for call in rpc.call_args_list))
        self.assertEqual(self.call("status")["tasks"][0]["status"], "canceled")

    def test_concurrent_registration_plans_do_not_overwrite_binding(self):
        first = self.call("connection_plan", resourceType="mcp", name="test-mcp")
        second = self.call("connection_plan", resourceType="mcp", name="test-mcp",
                           auth={"type": "bearer", "tokenEnv": "MCP_SEPARATE_TOKEN"})
        self.call("apply", planId=first["id"])
        result = self.call("apply", planId=second["id"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error"], "conflict")
        self.assertEqual(self.call("status")["connections"][0]["auth"], {"type": "none"})

    def test_jsonrpc_tools_and_errors_keep_connection_alive(self):
        requests = ["not json", json.dumps({"jsonrpc": "2.0", "id": 0, "method": "tools/list"})]
        requests += [json.dumps(value) for value in (
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "nacos_status", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "nacos_credentials_save", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 5, "method": "resources/list"},
            {"jsonrpc": "2.0", "id": 6, "method": "ping"})]
        sink = io.StringIO()
        serve(self.service, io.StringIO("\n".join(requests) + "\n"), sink)
        results = [json.loads(line) for line in sink.getvalue().splitlines()]
        self.assertEqual(results[2]["result"]["serverInfo"]["version"], __version__)
        self.assertEqual(results[2]["result"]["capabilities"], {"tools": {}})
        self.assertEqual(results[4]["result"]["structuredContent"]["host"]["name"], "Qoder")
        self.assertTrue(results[5]["result"]["isError"])
        self.assertEqual(results[6]["error"]["code"], -32601)
        self.assertEqual(results[7]["result"], {})

    def test_single_address_login_defaults_to_shared_admin_without_request(self):
        service = self.fresh_service()
        profile = {"namespaceId": "single", "clientUrl": "https://single.example.org/nacos/",
                   "allowedOperations": ["read", "develop"], "clientAuth": self.login_auth()}
        with patch.dict("os.environ", {"SYNTHETIC_USER": "test-user", "SYNTHETIC_PASSWORD": "test-password"}, clear=True):
            result = service.invoke("configure", {"profile": profile, "expectedRevision": 0})
            self.assertEqual(result["configurationRevision"], 1)
            self.assertEqual(result["connection"], "unverified")
            saved = result["profile"]
            self.assertEqual(saved["adminMode"], "shared")
            self.assertEqual(saved["adminUrl"], saved["clientUrl"])
            self.assertEqual(saved["clientUrl"], profile["clientUrl"].rstrip("/"))
            self.assertEqual(saved["adminAuth"], self.login_auth())
            self.assertEqual(saved["id"], "synthetic-host")
            self.assertEqual(saved["identityId"], "synthetic-user")
            self.assertEqual(service.invoke("status")["diagnosis"], {"status": "not_checked"})
            self.assertEqual(result["credentialStatus"]["admin"]["status"], "ready")
        self.assertEqual(self.remote.calls, [])

    def test_shared_login_uses_single_address_for_synthetic_client_and_admin_requests(self):
        from urllib.parse import parse_qs, urlsplit

        service = self.fresh_service("shared-http", Registry)
        url = "https://single.example.org/nacos"
        profile = {"namespaceId": "synthetic", "clientUrl": url, "allowedOperations": ["read", "develop"],
                   "clientAuth": self.login_auth()}
        credentials = {"SYNTHETIC_USER": "synthetic-user", "SYNTHETIC_PASSWORD": "synthetic-password"}
        requests = []

        def http(address, method="GET", headers=None, data=None, **kwargs):
            requests.append((address, method, headers, data))
            self.assertTrue(address.startswith(url + "/"))
            if address == url + "/v3/auth/user/login":
                self.assertEqual(method, "POST")
                self.assertEqual(parse_qs(data.decode()), {"username": [credentials["SYNTHETIC_USER"]],
                                                           "password": [credentials["SYNTHETIC_PASSWORD"]]})
                return 200, {}, json.dumps({"accessToken": "synthetic-session-token", "tokenTtl": 3600}).encode()
            self.assertEqual(method, "GET")
            self.assertEqual(headers["accessToken"], "synthetic-session-token")
            self.assertEqual(parse_qs(urlsplit(address).query)["namespaceId"], ["synthetic"])
            if urlsplit(address).path == "/nacos/v3/client/ai/resources/search":
                response = {"items": []}
            elif urlsplit(address).path == "/nacos/v3/admin/ai/skills":
                response = {"name": "sample-skill", "scope": "PRIVATE", "versions": []}
            else:
                self.fail("Unexpected synthetic HTTP route: " + address)
            return 200, {}, json.dumps({"code": 0, "data": response}).encode()

        with patch.dict("os.environ", credentials, clear=True), \
                patch("nacos_registry.registry.http", side_effect=http) as transport:
            configured = service.invoke("configure", {"profile": profile, "expectedRevision": 0})
            transport.assert_not_called()
            diagnosis = service.invoke("diagnose")
            self.assertEqual(diagnosis["clientRead"], "passed")
            self.assertEqual(service.invoke("skill_status", {"name": "sample-skill"})["metadata"]["scope"], "PRIVATE")
            self.assertEqual(service.invoke("status")["diagnosis"], diagnosis)
            self.assertEqual(configured["profile"]["adminAuth"], configured["profile"]["clientAuth"])
        self.assertEqual([method for _, method, _, _ in requests], ["POST", "GET", "POST", "GET"])
        self.assertEqual(self.remote.calls, [])

    def test_shared_admin_follows_client_and_rejects_conflicting_fields(self):
        self.configure_login()
        revision = self.call("status")["configurationRevision"]
        changed = {"namespaceId": "test", "clientUrl": "https://new.example.org/nacos",
                   "allowedOperations": self.profile["allowedOperations"]}
        self.assert_rejected_without_save("configure", {"profile": changed, "expectedRevision": revision}, "permission")
        result = self.call("configure", profile=changed, authorizeCredentialReuse=True)
        self.assertEqual(result["profile"]["adminMode"], "shared")
        self.assertEqual(result["profile"]["adminUrl"], changed["clientUrl"])
        self.assertEqual(result["profile"]["adminAuth"], self.login_auth())
        for extra in ({"adminUrl": "https://conflicting.example.org/nacos"}, {"adminAuth": {"type": "none"}}):
            with self.subTest(extra=extra):
                self.assert_rejected_without_save("configure", {
                    "profile": {**changed, "adminMode": "shared", **extra},
                    "expectedRevision": result["configurationRevision"]}, "validation")
        self.assertEqual(self.remote.calls, [])

    def test_independent_admin_and_omitted_identity_roots_are_preserved(self):
        original = self.call("configure", profile={**self.profile, "adminMode": "independent",
                                                  "adminUrl": "https://admin.example.org/nacos",
                                                  "adminAuth": self.login_auth()})["profile"]
        with patch("nacos_qoder.host.socket.gethostname", return_value="changed-host"), \
                patch("nacos_qoder.host.getpass.getuser", return_value="changed-user"):
            result = self.call("configure", profile={"namespaceId": "new-namespace",
                                                    "clientUrl": "https://client.example.org/nacos",
                                                    "allowedOperations": ["read", "develop"]})
        for field in ("id", "identityId", "scanRoots", "installRoots", "adminMode", "adminUrl", "adminAuth"):
            self.assertEqual(result["profile"][field], original[field], field)
        self.assertEqual(result["profile"]["id"], "test")
        self.assertEqual(self.remote.calls, [])

    def test_existing_profile_accepts_only_confirmed_changes_but_fresh_profile_requires_connection(self):
        self.assertEqual(DEFINITIONS["configure"][1]["properties"]["profile"]["required"], [])
        before = self.call("status")["profile"]
        updated = self.call("configure", profile={"displayName": "Confirmed display only"})["profile"]
        self.assertEqual(updated, {**before, "displayName": "Confirmed display only"})
        fresh = self.fresh_service("incomplete-fresh")
        with self.assertRaises(PluginError):
            fresh.invoke("configure", {"profile": {"displayName": "Incomplete"}, "expectedRevision": 0})
        self.assertFalse(fresh.store.file.exists())
        self.assertEqual(self.remote.calls, [])

    def test_generated_id_survives_hostname_change_on_later_save(self):
        service = self.fresh_service()
        profile = {"namespaceId": "test", "clientUrl": self.profile["clientUrl"], "allowedOperations": ["read"]}
        first = service.invoke("configure", {"profile": profile, "expectedRevision": 0})
        with patch("nacos_qoder.host.socket.gethostname", return_value="different-host"), \
                patch("nacos_qoder.host.getpass.getuser", return_value="different-user"):
            second = service.invoke("configure", {"profile": profile, "expectedRevision": 1})
        self.assertEqual(second["profile"]["id"], first["profile"]["id"])
        self.assertEqual(second["profile"]["identityId"], first["profile"]["identityId"])

    def test_new_credential_references_do_not_require_reuse_authorization(self):
        self.configure_login()
        result = self.call("configure", profile={"namespaceId": "test", "clientUrl": "https://new.example.org/nacos",
                                                "allowedOperations": ["read"],
                                                "clientAuth": {"type": "token", "tokenEnv": "NEW_SYNTHETIC_TOKEN"}})
        self.assertEqual(result["profile"]["adminAuth"], result["profile"]["clientAuth"])
        self.assertEqual(result["credentialStatus"]["client"]["status"], "missing")
        self.assertEqual(self.remote.calls, [])

    def test_independent_admin_target_change_requires_explicit_credential_reuse(self):
        result = self.call("configure", profile={**self.profile, "adminAuth": self.login_auth()})
        changed = {**self.profile, "adminUrl": "https://other-admin.example.org/nacos"}
        self.assert_rejected_without_save("configure", {"profile": changed,
                                                       "expectedRevision": result["configurationRevision"]}, "permission")
        saved = self.call("configure", profile=changed, authorizeCredentialReuse=True)
        self.assertEqual(saved["profile"]["adminAuth"], self.login_auth())
        self.assertEqual(saved["profile"]["clientAuth"], {"type": "none"})

    def test_explicit_empty_roots_stay_empty_without_default_opt_in(self):
        default = self.root / "home/.qoder/skills"
        default.mkdir(parents=True)
        result = self.call("configure", profile={**self.profile, "scanRoots": [], "installRoots": []})
        self.assertEqual(result["profile"]["scanRoots"], [])
        self.assertEqual(result["profile"]["installRoots"], [])
        result = self.call("configure", profile={"namespaceId": "test", "clientUrl": self.profile["clientUrl"],
                                                "allowedOperations": ["read"]})
        self.assertEqual(result["profile"]["scanRoots"], [])
        self.assertEqual(result["profile"]["installRoots"], [])
        self.assertEqual(self.call("scan")["rootStates"], [])

    def test_default_roots_append_deduplicate_and_preserve_order(self):
        default = self.root / "home/.qoder/skills"
        default.mkdir(parents=True)
        first, second = str(self.source.parent), str(self.root / "other-skills")
        result = self.call("configure", profile={**self.profile, "scanRoots": [second, first, second],
                                                "installRoots": [str(default), second, str(default)]}, addDefaultRoots=True)
        self.assertEqual(result["profile"]["scanRoots"], [second, first, str(default)])
        self.assertEqual(result["profile"]["installRoots"], [str(default), second])
        again = self.call("configure", profile={"namespaceId": "test", "clientUrl": self.profile["clientUrl"],
                                               "allowedOperations": ["read"]}, addDefaultRoots=True)
        self.assertEqual(again["profile"]["scanRoots"], result["profile"]["scanRoots"])
        self.assertEqual(again["profile"]["installRoots"], result["profile"]["installRoots"])
        self.assertEqual(self.remote.calls, [])

    def test_root_limits_apply_after_dedup_and_default_append_without_save_on_error(self):
        default = self.root / "home/.qoder/skills"
        default.mkdir(parents=True)
        roots = [str(self.root / ("skills-" + str(i))) for i in range(16)]
        result = self.call("configure", profile={**self.profile, "scanRoots": roots + [roots[0]], "installRoots": roots})
        self.assertEqual(result["profile"]["scanRoots"], roots)
        for field in ("scanRoots", "installRoots"):
            for add_defaults in (False, True):
                with self.subTest(field=field, add_defaults=add_defaults):
                    profile = {**result["profile"], field: roots if add_defaults else roots + [str(self.root / "overflow")]}
                    self.assert_rejected_without_save("configure", {"profile": profile,
                        "expectedRevision": result["configurationRevision"], "addDefaultRoots": add_defaults}, "validation")

    def test_configure_schema_requires_revision_and_boolean_choices(self):
        valid = {"profile": self.profile, "expectedRevision": 1}
        validate(valid, DEFINITIONS["configure"][1])
        for args in ({"profile": self.profile}, {**valid, "expectedRevision": True},
                     {**valid, "expectedRevision": "1"}, {**valid, "authorizeCredentialReuse": 1},
                     {**valid, "addDefaultRoots": "yes"}):
            with self.subTest(args=args), self.assertRaises(PluginError):
                validate(args, DEFINITIONS["configure"][1])
        for revision in (-1, True, "1"):
            self.assert_rejected_without_save("configure", {"profile": self.profile,
                                                           "expectedRevision": revision}, "validation")

    def test_same_profile_save_increments_revision_clears_diagnosis_and_stales_plan(self):
        status = self.call("status")
        plan = self.call("connection_plan", resourceType="mcp", name="test-mcp")
        self.assertEqual(plan["authorizationContext"], status["context"])
        self.assertEqual(plan["configurationRevision"], status["configurationRevision"])
        self.call("diagnose")
        result = self.call("configure", profile=status["profile"])
        self.assertEqual(result["profile"], status["profile"])
        self.assertEqual(result["configurationRevision"], status["configurationRevision"] + 1)
        self.assertNotEqual(result["context"], status["context"])
        self.assertEqual(self.call("status")["diagnosis"], {"status": "not_checked"})
        self.assert_rejected_without_save("apply", {"planId": plan["id"]})

    def test_revision_prevents_aba_and_stale_save_does_not_touch_disk(self):
        before = self.call("status")
        plan = self.call("connection_plan", resourceType="mcp", name="test-mcp")
        self.call("configure", profile={**before["profile"], "namespaceId": "other"})
        restored = self.call("configure", profile=before["profile"])
        self.assertEqual(restored["profile"], before["profile"])
        self.assertEqual(restored["configurationRevision"], before["configurationRevision"] + 2)
        self.assertNotEqual(restored["context"], before["context"])
        self.assert_rejected_without_save("configure", {"profile": before["profile"],
                                                       "expectedRevision": before["configurationRevision"]})
        self.assert_rejected_without_save("apply", {"planId": plan["id"]})
        with self.assertRaises(PluginError) as caught:
            self.service.invoke("status", expected_context=before["context"])
        self.assertEqual(caught.exception.kind, "conflict")

    def test_competing_services_only_one_configuration_revision_is_saved(self):
        revision = self.call("status")["configurationRevision"]
        services = [Service(Store(self.service.store.root), lambda *_: self.remote) for _ in range(2)]
        barrier = threading.Barrier(2)
        results, errors = [], []

        def save(service, namespace):
            try:
                barrier.wait(timeout=5)
                results.append(service.invoke("configure", {"profile": {**self.profile, "namespaceId": namespace},
                                                            "expectedRevision": revision}))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=save, args=(service, "competitor-" + str(i)))
                   for i, service in enumerate(services)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], PluginError)
        self.assertEqual(errors[0].kind, "conflict")
        self.assertEqual(self.call("status")["configurationRevision"], revision + 1)
        self.assertEqual(self.call("status")["profile"], results[0]["profile"])
        stale = {"profile": {**self.profile, "namespaceId": "loser"}, "expectedRevision": revision}
        self.assert_rejected_without_save("configure", stale, service=services[0])
        self.assertEqual(self.remote.calls, [])

    def test_tool_context_rejects_configuration_and_environment_changes_before_work(self):
        with patch.dict("os.environ", {"SYNTHETIC_USER": "user", "SYNTHETIC_PASSWORD": "first"}, clear=True):
            saved = self.configure_login()
            self.assertFalse(call_tool(self.service, "nacos_status", {"_context": saved["context"]})["isError"])
            disk = self.service.store.file.read_bytes()
            os.environ["SYNTHETIC_PASSWORD"] = "second"
            for action, args in (("nacos_scan", {}), ("nacos_diagnose", {}), ("nacos_configure", {
                    "profile": self.profile, "expectedRevision": saved["configurationRevision"]})):
                with self.subTest(action=action), self.assertRaises(PluginError) as caught:
                    call_tool(self.service, action, {**args, "_context": saved["context"]})
                self.assertEqual(caught.exception.kind, "conflict")
                self.assertEqual(self.service.store.file.read_bytes(), disk)
            current = self.call("status")
            self.call("configure", profile=current["profile"])
            with self.assertRaises(PluginError) as caught:
                call_tool(self.service, "nacos_search", {"_context": current["context"]})
            self.assertEqual(caught.exception.kind, "conflict")
        self.assertEqual(self.remote.calls, [])

    def test_diagnosis_success_is_persisted_only_after_read_only_probe(self):
        observed = []

        def search(**kwargs):
            record = json.loads(self.service.store.file.read_text())["diagnosis"]
            observed.append(record)
            self.assertEqual(record["status"], "checking")
            self.assertNotIn("clientRead", record)
            self.assertNotIn("checkedAt", record)
            self.assertEqual(kwargs, {"query": "", "limit": 1})
            return {"items": [{"name": "synthetic-resource"}]}

        with patch.object(self.remote, "search", side_effect=search) as probe:
            result = self.call("diagnose")
        probe.assert_called_once_with(query="", limit=1)
        self.assertEqual(len(observed), 1)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["clientRead"], "passed")
        self.assertEqual(result["adminWrite"], "not_probed")
        self.assertEqual(result["resourceCount"], 1)
        self.assertGreaterEqual(result["checkedAt"], result["startedAt"])
        self.assertEqual(self.call("status")["diagnosis"], result)
        self.assertEqual(Service(Store(self.service.store.root), lambda *_: self.remote).invoke("status")["diagnosis"], result)
        self.assertEqual(self.remote.calls, [])

    def test_diagnosis_failure_persists_safe_error_and_reraises(self):
        failure = PluginError("authentication", "Registry login credentials were rejected")

        def search(**kwargs):
            self.assertEqual(json.loads(self.service.store.file.read_text())["diagnosis"]["status"], "checking")
            raise failure

        with patch.object(self.remote, "search", side_effect=search) as probe:
            with self.assertRaises(PluginError) as caught:
                self.call("diagnose")
        self.assertIs(caught.exception, failure)
        probe.assert_called_once_with(query="", limit=1)
        result = self.call("status")["diagnosis"]
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["clientRead"], "failed")
        self.assertEqual(result["error"], failure.result())
        self.assertGreaterEqual(result["checkedAt"], result["startedAt"])
        self.assertEqual(Service(Store(self.service.store.root), lambda *_: self.remote).invoke("status")["diagnosis"], result)
        self.assertEqual(self.remote.calls, [])

    def test_interrupted_diagnosis_is_unknown_not_success_after_restart(self):
        with patch.object(self.remote, "search", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.call("diagnose")
        persisted = json.loads(self.service.store.file.read_text())["diagnosis"]
        self.assertEqual(persisted["status"], "checking")
        restarted = Service(Store(self.service.store.root), lambda *_: self.remote)
        before = restarted.store.file.read_bytes()
        diagnosis = restarted.invoke("status")["diagnosis"]
        self.assertEqual(diagnosis["status"], "result_unknown")
        self.assertNotIn("clientRead", diagnosis)
        self.assertEqual(restarted.store.file.read_bytes(), before)
        self.assertEqual(self.remote.calls, [])

    def test_status_discards_diagnosis_from_a_different_authorization_context(self):
        self.call("diagnose")
        with self.service.store.locked():
            self.service.store.data["diagnosis"]["context"] = "stale-context"
            self.service.store.save()
        disk = self.service.store.file.read_bytes()
        self.assertEqual(self.call("status")["diagnosis"], {"status": "not_checked"})
        self.assertEqual(self.service.store.file.read_bytes(), disk)

    def test_credential_environment_change_invalidates_diagnosis_not_revision(self):
        with patch.dict("os.environ", {"SYNTHETIC_USER": "user", "SYNTHETIC_PASSWORD": "first"}, clear=True):
            saved = self.configure_login()
            result = self.call("diagnose")
            self.assertEqual(self.call("status")["diagnosis"], result)
            disk = self.service.store.file.read_bytes()
            os.environ["SYNTHETIC_PASSWORD"] = "second"
            status = self.call("status")
            self.assertEqual(status["configurationRevision"], saved["configurationRevision"])
            self.assertNotEqual(status["context"], saved["context"])
            self.assertEqual(status["diagnosis"], {"status": "not_checked"})
            self.assertEqual(self.service.store.file.read_bytes(), disk)
            os.environ["UNREFERENCED_SYNTHETIC_VALUE"] = "irrelevant"
            self.assertEqual(self.call("status")["context"], status["context"])
        self.assertEqual(self.remote.calls, ["search"])

    def test_credential_status_missing_login_never_downgrades_to_anonymous(self):
        self.configure_login()
        self.service.registry_factory = Registry
        for env, fields in (({}, {"usernameEnv": "missing", "passwordEnv": "missing"}),
                            ({"SYNTHETIC_USER": "user"}, {"usernameEnv": "set", "passwordEnv": "missing"}),
                            ({"SYNTHETIC_USER": "user", "SYNTHETIC_PASSWORD": ""}, {"usernameEnv": "set", "passwordEnv": "missing"})):
            with self.subTest(fields=fields), patch.dict("os.environ", env, clear=True):
                status = self.call("status")
                for role in ("client", "admin"):
                    self.assertEqual(status["credentialStatus"][role], {"type": "login", "source": "environment",
                                                                      "fields": fields, "status": "missing"})
                self.assert_rejected_without_save("search", {}, "authentication")
                self.assertEqual(self.call("status")["profile"]["clientAuth"], self.login_auth())
        self.assertEqual(self.remote.calls, [])

    def test_credential_status_reports_independent_ready_missing_and_not_required(self):
        self.assertEqual(self.call("status")["credentialStatus"]["client"], {
            "type": "none", "source": "none", "fields": {}, "status": "not_required"})
        with patch.dict("os.environ", {"SYNTHETIC_TOKEN": "synthetic-value"}, clear=True):
            result = self.call("configure", profile={**self.profile,
                "clientAuth": {"type": "token", "tokenEnv": "SYNTHETIC_TOKEN"}, "adminAuth": self.login_auth()})
            self.assertEqual(result["credentialStatus"]["client"], {"type": "token", "source": "environment",
                                                                   "fields": {"tokenEnv": "set"}, "status": "ready"})
            self.assertEqual(result["credentialStatus"]["admin"]["status"], "missing")
            os.environ["SYNTHETIC_USER"], os.environ["SYNTHETIC_PASSWORD"] = "user", "password"
            self.assertEqual(self.call("status")["credentialStatus"]["admin"]["status"], "ready")

    def test_authorization_context_is_stable_across_services_and_new_process(self):
        env = {"HOME": str(self.root / "home"), "SYNTHETIC_USER": "user", "SYNTHETIC_PASSWORD": "first"}
        with patch.dict("os.environ", env, clear=True):
            saved = self.configure_login()
            key = (self.service.store.root / ".credential-key").read_bytes()
            other = Service(Store(self.service.store.root), lambda *_: self.remote)
            self.assertEqual(other.invoke("status")["context"], saved["context"])
            source = Path(__file__).resolve().parents[1] / "src"
            code = ("import json,sys; from nacos_qoder.service import Service; "
                    "from nacos_registry.store import Store; "
                    "print(json.dumps(Service(Store(sys.argv[1])).invoke('status')))")
            dependencies = Path(package.yaml.__file__).resolve().parents[1]
            pythonpath = os.pathsep.join((str(source), str(dependencies)))
            process = subprocess.run([sys.executable, "-S", "-B", "-c", code, str(self.service.store.root)],
                cwd=self.root, env={**env, "PYTHONPATH": pythonpath}, capture_output=True, text=True, timeout=15)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stderr, "")
            status = json.loads(process.stdout)
            self.assertEqual(status["context"], saved["context"])
            self.assertEqual(status["configurationRevision"], saved["configurationRevision"])
            self.assertEqual((self.service.store.root / ".credential-key").read_bytes(), key)
            os.environ["SYNTHETIC_PASSWORD"] = "second"
            self.assertNotEqual(other.invoke("status")["context"], saved["context"])
        self.assertEqual(self.remote.calls, [])

    def test_authorization_context_uses_private_random_hmac_key_under_lock(self):
        with patch.dict("os.environ", {"SYNTHETIC_USER": "user", "SYNTHETIC_PASSWORD": "password"}, clear=True):
            saved = self.configure_login()
            key_path = self.service.store.root / ".credential-key"
            key = key_path.read_bytes()
            self.assertEqual(len(key), 32)
            self.assertEqual(stat.S_IMODE(key_path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(self.service.store.root.stat().st_mode), 0o700)
            self.assertEqual(key_path.stat().st_uid, os.getuid())
            self.assertEqual(key_path.stat().st_nlink, 1)
            refs = {role: {field: {"reference": ref, "value": os.environ[ref]}
                           for field, ref in self.login_auth().items() if field.endswith("Env")}
                    for role in ("clientAuth", "adminAuth")}
            payload = json.dumps(refs, sort_keys=True, separators=(",", ":")).encode()
            fingerprint = hmac.new(key, payload, hashlib.sha256).hexdigest()
            expected = digest({"profile": saved["profile"], "configurationRevision": saved["configurationRevision"],
                               "credentialFingerprint": fingerprint})
            self.assertEqual(saved["context"], expected)
            with self.assertRaises(PluginError):
                self.service.store.authorization_context()
            with self.assertRaises(PluginError):
                self.service.store._credential_key()
            other = self.fresh_service("different-key")
            other_saved = other.invoke("configure", {"profile": saved["profile"], "expectedRevision": 0})
            # Match revisions so only the random per-store key accounts for the difference.
            with other.store.locked():
                other.store.data["configurationRevision"] = saved["configurationRevision"]
                other.store.save()
            self.assertNotEqual(other.invoke("status")["context"], expected)
            self.assertNotEqual((other.store.root / ".credential-key").read_bytes(), key)
            self.assertEqual(other_saved["profile"], saved["profile"])
            self.assertNotIn(key.hex(), self.service.store.file.read_text())
            self.assertNotIn(fingerprint, self.service.store.file.read_text())

    def test_credential_key_rejects_nonprivate_mode_and_invalid_length(self):
        self.configure_login()
        key_path = self.service.store.root / ".credential-key"
        key = key_path.read_bytes()
        for mode, content in ((0o644, key), (0o600, b"short"), (0o600, b"x" * 33)):
            with self.subTest(mode=mode, length=len(content)):
                key_path.write_bytes(content)
                key_path.chmod(mode)
                self.assert_rejected_without_save("status", {}, "validation")
        key_path.write_bytes(key)
        key_path.chmod(0o600)
        self.assertEqual(self.call("status")["credentialStatus"]["client"]["status"], "missing")
        self.service.store.root.chmod(0o755)
        self.assert_rejected_without_save("status", {}, "validation")
        self.service.store.root.chmod(0o700)

    def test_credential_key_and_directory_require_current_uid(self):
        self.configure_login()
        uid = os.getuid()
        with patch("nacos_registry.store.os.getuid", return_value=uid + 1):
            self.assert_rejected_without_save("status", {}, "validation")
        original_fstat = os.fstat

        def foreign_key(descriptor):
            metadata = original_fstat(descriptor)
            if stat.S_ISREG(metadata.st_mode) and metadata.st_size == 32:
                values = list(metadata)
                values[4] = uid + 1
                return os.stat_result(values)
            return metadata

        with patch("nacos_registry.store.os.fstat", side_effect=foreign_key):
            self.assert_rejected_without_save("status", {}, "validation")

    def test_credential_key_rejects_symlink_and_hardlink_without_reading_target(self):
        configured = self.configure_login()
        key_path = self.service.store.root / ".credential-key"
        original = key_path.read_bytes()
        target = self.root / "synthetic-key-target"
        target.write_bytes(b"synthetic-not-a-credential-key")
        key_path.unlink()
        key_path.symlink_to(target)
        with patch("nacos_registry.store.os.read", side_effect=AssertionError("Do not read a linked key")) as read_key:
            self.assert_rejected_without_save("status", {}, "validation")
        read_key.assert_not_called()
        self.assertEqual(target.read_bytes(), b"synthetic-not-a-credential-key")
        key_path.unlink()
        key_path.write_bytes(original)
        key_path.chmod(0o600)
        duplicate = self.root / "duplicate-key"
        os.link(key_path, duplicate)
        self.assert_rejected_without_save("status", {}, "validation")
        duplicate.unlink()
        self.assertEqual(self.call("status")["context"], configured["context"])

    def test_only_environment_replacement_stales_plan_but_preserves_installations(self):
        with patch.dict("os.environ", {"SYNTHETIC_USER": "user", "SYNTHETIC_PASSWORD": "first"}, clear=True):
            saved = self.configure_login()
            installed = self.install()["result"]
            plan = self.call("uninstall_plan", installationId=installed["id"])
            self.assertEqual(plan["context"], digest(saved["profile"]))
            self.assertEqual(plan["authorizationContext"], saved["context"])
            os.environ["SYNTHETIC_PASSWORD"] = "second"
            current = self.call("status")
            self.assertEqual(current["profile"], saved["profile"])
            self.assertEqual(current["configurationRevision"], saved["configurationRevision"])
            self.assertEqual(current["installations"], [installed])
            self.assertNotEqual(current["context"], saved["context"])
            calls = list(self.remote.calls)
            self.assert_rejected_without_save("apply", {"planId": plan["id"]})
            self.assertEqual(self.remote.calls, calls)
            self.assertTrue(Path(installed["target"]).is_dir())
            self.assertEqual(self.call("verify_skill", installationId=installed["id"])["files"], "verified")
            fresh = self.call("uninstall_plan", installationId=installed["id"])
            self.assertEqual(self.call("apply", planId=fresh["id"])["status"], "completed")

    def test_synthetic_credentials_never_enter_state_status_or_tool_results(self):
        # Construct whole sentinels at runtime so source-input checks cannot match the test itself.
        values = {"SYNTHETIC_USER": "synthetic-" + "user-marker-2026",
                  "SYNTHETIC_PASSWORD": "synthetic-" + "password-marker-2026"}
        with patch.dict("os.environ", values, clear=True):
            saved = self.configure_login()
            results = [saved, call_tool(self.service, "nacos_status", {}),
                       call_tool(self.service, "nacos_diagnose", {})]
            args = self.upload_args()
            preview = call_tool(self.service, "nacos_upload_preview", args)
            results.append(preview)
            planned = call_tool(self.service, "nacos_upload_plan", {
                **args, "expectedContentHash": preview["structuredContent"]["contentHash"]})
            results.append(planned)
            results.append(call_tool(self.service, "nacos_apply", {"planId": planned["structuredContent"]["id"]}))
            results.append(call_tool(self.service, "nacos_status", {}))
            serialized = json.dumps(results)
            state = self.service.store.file.read_text()
            for value in values.values():
                self.assertNotIn(value, serialized)
                self.assertNotIn(value, state)
                for artifact in (self.service.store.root / "artifacts").iterdir():
                    self.assertNotIn(value.encode(), artifact.read_bytes())
            self.assertIn("SYNTHETIC_PASSWORD", state)
            self.assertEqual(self.call("status")["profile"]["clientAuth"], self.login_auth())

    def test_raw_http_failure_secret_is_omitted_from_diagnosis_and_stdio_result(self):
        from urllib.error import HTTPError
        from nacos_registry.transport import http

        secret = "synthetic-" + "token-response-marker-2026"
        with patch.dict("os.environ", {"SYNTHETIC_TOKEN": secret}, clear=True):
            self.call("configure", profile={**self.profile, "adminMode": "shared",
                "clientAuth": {"type": "token", "tokenEnv": "SYNTHETIC_TOKEN"},
                "adminAuth": {"type": "token", "tokenEnv": "SYNTHETIC_TOKEN"}})
            self.service.registry_factory = Registry
            failure = HTTPError(self.profile["clientUrl"], 401, secret, {},
                                io.BytesIO(json.dumps({"message": secret}).encode()))
            requests = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                 "params": {"name": "nacos_diagnose", "arguments": {}}},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                 "params": {"name": "nacos_status", "arguments": {}}},
            ]
            sink = io.StringIO()
            with patch("nacos_registry.registry.http", new=http), \
                    patch("nacos_registry.transport.request.build_opener") as opener:
                opener.return_value.open.side_effect = failure
                serve(self.service, io.StringIO("\n".join(json.dumps(item) for item in requests) + "\n"), sink)
            opener.return_value.open.assert_called_once()
            result = json.loads(sink.getvalue().splitlines()[1])["result"]
            self.assertTrue(result["isError"])
            self.assertEqual(json.loads(result["content"][0]["text"])["error"], "authentication")
            diagnosis = self.call("status")["diagnosis"]
            self.assertEqual(diagnosis["status"], "failed")
            self.assertEqual(diagnosis["error"]["message"], "HTTP request rejected; response content omitted")
            self.assertNotIn(secret, sink.getvalue())
            self.assertNotIn(secret, self.service.store.file.read_text())

    def test_build_manifest_inputs_do_not_include_synthetic_secrets_or_local_state(self):
        script = Path(__file__).resolve().parents[1] / "scripts/build.py"
        spec = importlib.util.spec_from_file_location("qoder_test_build", script)
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        root = self.root / "synthetic-build"
        root.mkdir()
        for name in builder.SOURCE_DIRS:
            (root / name).mkdir()
        (root / "LICENSE").write_text("Synthetic test license")
        project = Path(__file__).resolve().parents[1]
        # Only the explicit, shipped nonsecret manifests are read, never host connector configuration.
        (root / ".qoder-plugin/plugin.json").write_bytes((project / ".qoder-plugin/plugin.json").read_bytes())
        for name in builder.SOURCE_FILES:
            (root / name).write_bytes((project / name).read_bytes() if name == ".mcp.json" else b"")
        secret = "synthetic-" + "build-exclusion-marker-2026"
        with patch.dict("os.environ", {"SYNTHETIC_PASSWORD": secret}, clear=True):
            service = Service(Store(root / "src/.qoder/state"), lambda *_: self.remote)
            service.invoke("configure", {"profile": {**self.profile, "clientAuth": self.login_auth()}, "expectedRevision": 0})
            for name in (".env", ".env.test", "state.json", "credentials.json"):
                (root / "src" / name).write_text(secret)
            with patch.object(builder, "dependency_sources", return_value={}):
                inputs, _ = builder.source_inputs(root)
            self.assertIn("qoder/.qoder-plugin/plugin.json", inputs)
            self.assertIn("qoder/.mcp.json", inputs)
            for name, data in inputs.items():
                self.assertNotIn(secret.encode(), data, name)
                self.assertNotIn(".credential-key", name)
                self.assertNotIn("state.json", name)
                self.assertNotIn("credentials.json", name)
                self.assertNotIn(".env", name)
            manifest = json.loads(inputs["qoder/.mcp.json"])
            server = manifest["mcpServers"]["nacos-ai-registry"]
            self.assertEqual(server["args"], ["${QODER_PLUGIN_ROOT}/server/nacos-qoder.pyz", "serve"])
            self.assertNotIn("env", server)
            self.assertNotIn("headers", server)
            self.assertEqual(json.loads(inputs["qoder/.qoder-plugin/plugin.json"])["mcpServers"], "./.mcp.json")
        self.assertFalse((root / "dist").exists())

    def test_repeated_inventory_preserves_stable_ignore_track_and_explicit_selection(self):
        first = self.call("scan")
        item = first["items"][0]
        self.assertEqual(item["selection"], "unselected")
        for action in ("ignore", "track", "ignore", "track"):
            selected = self.call("select", scanId=first["id"], selections=[{"candidateId": item["id"], "action": action}])
            self.assertEqual(selected["results"][0]["status"], action)
            second = self.call("scan")
            self.assertNotEqual(first["id"], second["id"])
            self.assertEqual(second["items"][0]["id"], item["id"])
            self.assertEqual(second["items"][0]["selection"], action)
            self.assertEqual(second["items"][0]["binding"], selected["results"][0]["bindingId"])
            first = second
        self.assertEqual(self.remote.calls, [])
        _, uploaded = self.upload_draft()
        self.assertEqual(uploaded["status"], "completed")
        after = self.call("scan")
        self.assertEqual(after["items"][0]["id"], item["id"])
        self.assertEqual(after["items"][0]["selection"], "explicit")
        self.assertEqual(self.remote.calls.count("upload"), 1)

    def test_scan_root_states_and_metadata_inventory_do_not_hash_or_network(self):
        empty, missing, not_directory, unreadable = [self.root / name for name in ("empty", "missing", "file", "unreadable")]
        empty.mkdir()
        not_directory.write_text("Not a directory")
        unreadable.mkdir()
        roots = [str(path) for path in (self.source.parent, empty, missing, not_directory, unreadable)]
        self.call("configure", profile={**self.profile, "scanRoots": roots})
        original_iterdir = Path.iterdir

        def iterdir(path):
            if path == unreadable:
                raise PermissionError("Synthetic unreadable root")
            return original_iterdir(path)

        with patch.object(Path, "iterdir", new=iterdir), \
                patch.object(package, "hashes", side_effect=AssertionError("Inventory must not hash")), \
                patch.object(package, "disk_hashes", side_effect=AssertionError("Inventory must not hash disk")), \
                patch.object(package, "read_directory", side_effect=AssertionError("Inventory must read metadata only")), \
                patch.object(package, "pack", side_effect=AssertionError("Inventory must not package")):
            scan = self.call("scan")
        states = {item["root"]: item for item in scan["rootStates"]}
        self.assertEqual([item["root"] for item in scan["rootStates"]], roots)
        for path, expected, count in ((self.source.parent, "available", 1), (empty, "empty", 0),
                                      (missing, "missing", 0), (not_directory, "not_directory", 0),
                                      (unreadable, "unreadable", 0)):
            self.assertEqual(states[str(path)]["status"], expected)
            self.assertEqual(states[str(path)]["candidateCount"], count)
        self.assertEqual(self.remote.calls, [])

    def test_inventory_reports_unreadable_candidate_and_distinguishes_root_subsets(self):
        second_root = self.root / "other-root"
        second_source = second_root / "sample-skill"
        second_source.mkdir(parents=True)
        (second_source / "SKILL.md").write_bytes(skill()["SKILL.md"])
        self.call("configure", profile={**self.profile, "scanRoots": [str(self.source.parent), str(second_root)]})
        first = self.call("scan", roots=[str(self.source.parent)])
        second = self.call("scan", roots=[str(second_root)])
        self.assertNotEqual(first["items"][0]["id"], second["items"][0]["id"])
        self.assertEqual(first["items"][0]["name"], second["items"][0]["name"])
        self.assertEqual(second["roots"], [str(second_root)])
        self.assertEqual(len(second["rootStates"]), 1)
        self.assert_rejected_without_save("scan", {"roots": [str(self.root / "unconfigured")]}, "permission")
        original_read = Path.read_bytes

        def read(path):
            if path == second_source / "SKILL.md":
                raise PermissionError("Synthetic candidate permission failure")
            return original_read(path)

        with patch.object(Path, "read_bytes", new=read):
            result = self.call("scan", roots=[str(second_root)])
        self.assertEqual(result["items"][0]["status"], "unreadable")
        self.assertEqual(result["items"][0]["reason"], "permission")
        self.assertEqual(result["rootStates"][0]["candidateCount"], 0)
        self.assertEqual(self.remote.calls, [])

    def test_upload_preview_changed_content_is_rejected_before_precheck(self):
        args = self.upload_args()
        preview = self.call("upload_preview", **args)
        self.assertEqual(self.remote.calls, [])
        (self.source / "SKILL.md").write_bytes(skill("Changed after preview.")["SKILL.md"])
        with patch.object(self.remote, "precheck", wraps=self.remote.precheck) as precheck:
            self.assert_rejected_without_save("upload_plan", {**args, "expectedContentHash": preview["contentHash"]})
        precheck.assert_not_called()
        self.assertEqual(self.remote.calls, [])
        self.assertFalse((self.service.store.root / "artifacts").exists())

    def test_remote_advancement_and_remote_edit_preserve_bound_local_skill(self):
        _, uploaded = self.upload_draft()
        self.assertEqual(uploaded["status"], "completed")
        local = skill("A local edit to reconcile.")["SKILL.md"]
        (self.source / "SKILL.md").write_bytes(local)
        args = self.upload_args()
        baseline = copy.deepcopy(self.call("status")["bindings"])
        self.remote.meta["labels"] = {"latest": "2.0.0"}
        self.assert_rejected_without_save("upload_plan", args)
        self.assertEqual((self.source / "SKILL.md").read_bytes(), local)
        self.assertEqual(self.call("status")["bindings"], baseline)
        self.remote.meta.pop("labels")
        self.remote.content = skill("Remote draft edit.")
        with patch.object(self.remote, "precheck", wraps=self.remote.precheck) as precheck:
            self.assert_rejected_without_save("upload_plan", args)
        precheck.assert_not_called()
        self.assertEqual((self.source / "SKILL.md").read_bytes(), local)
        self.assertEqual(self.call("status")["bindings"], baseline)
        self.assertEqual(self.remote.calls.count("upload"), 1)

    def test_upload_local_edit_after_plan_fails_without_transmitting_write(self):
        args = self.upload_args()
        plan = self.call("upload_plan", **args)
        edited = skill("Local change after upload authorization.")["SKILL.md"]
        (self.source / "SKILL.md").write_bytes(edited)
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error"], "conflict")
        self.assertNotIn("upload", self.remote.calls)
        self.assertIsNone(self.remote.meta)
        self.assertEqual((self.source / "SKILL.md").read_bytes(), edited)
        self.assertEqual(self.call("status")["bindings"], [])

    def test_upload_remote_governance_changed_after_plan_is_not_overwritten(self):
        args = self.upload_args()
        plan = self.call("upload_plan", **args)
        remote = {"name": "sample-skill", "scope": "PUBLIC", "editingVersion": "2.0.0",
                  "versions": [{"version": "2.0.0", "status": "draft"}]}
        self.remote.meta = copy.deepcopy(remote)
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error"], "conflict")
        self.assertEqual(self.remote.meta, remote)
        self.assertNotIn("upload", self.remote.calls)
        self.assertEqual((self.source / "SKILL.md").read_bytes(), skill()["SKILL.md"])

    def test_install_remote_change_or_local_edit_after_plan_preserves_existing_files(self):
        installed = self.install()["result"]
        target = Path(installed["target"]) / "SKILL.md"
        self.remote.content = skill("Planned remote update.")
        plan = self.call("install_plan", name="sample-skill", installRoot=self.profile["installRoots"][0])
        self.remote.content = skill("Different remote update.")
        failed = self.call("apply", planId=plan["id"])
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["error"]["error"], "conflict")
        self.assertEqual(target.read_bytes(), skill()["SKILL.md"])
        self.assertEqual(self.call("status")["installations"], [installed])
        plan = self.call("install_plan", name="sample-skill", installRoot=self.profile["installRoots"][0])
        local = skill("Local edit after update plan.")["SKILL.md"]
        target.write_bytes(local)
        calls = list(self.remote.calls)
        failed = self.call("apply", planId=plan["id"])
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["error"]["error"], "conflict")
        self.assertEqual(self.remote.calls, calls)
        self.assertEqual(target.read_bytes(), local)
        self.assertEqual(self.call("status")["installations"], [installed])

    def test_unknown_upload_reconciles_exact_draft_without_resending_or_reapplying(self):
        args = self.upload_args()
        plan = self.call("upload_plan", **args)
        original_upload = self.remote.upload

        def lost_response(*args):
            original_upload(*args)
            raise PluginError("result_unknown", "Synthetic upload response lost")

        with patch.object(self.remote, "upload", side_effect=lost_response):
            unknown = self.call("apply", planId=plan["id"])
        self.assertEqual(unknown["status"], "result_unknown")
        self.assertEqual(self.remote.calls.count("upload"), 1)
        self.assertEqual(self.call("status")["bindings"], [])
        self.assertEqual(self.call("inspect_operation", operationId=unknown["id"])["status"], "result_unknown")
        self.assert_rejected_without_save("apply", {"planId": plan["id"]})
        remote_content = self.remote.content
        self.remote.content = skill("Not the attempted upload.")
        self.assert_rejected_without_save("reconcile", {"operationId": unknown["id"]}, "result_unknown")
        self.assertEqual(self.call("inspect_operation", operationId=unknown["id"])["status"], "result_unknown")
        self.remote.content = remote_content
        result = self.call("reconcile", operationId=unknown["id"], version="1.0.0")
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["reconciled"])
        self.assertEqual(self.call("status")["bindings"][0]["policy"], "explicit")
        calls = list(self.remote.calls)
        for _ in range(2):
            replay = self.call("apply", planId=plan["id"])
            self.assertEqual(replay["id"], unknown["id"])
            self.assertEqual(replay["status"], "completed")
        self.assertEqual(self.remote.calls, calls)
        self.assertEqual(self.remote.calls.count("upload"), 1)
        self.assert_rejected_without_save("reconcile", {"operationId": unknown["id"]}, "validation")

    def test_unknown_lifecycle_reconciliation_does_not_repeat_submit_or_publish(self):
        for action in ("submit", "publish"):
            with self.subTest(action=action):
                remote = FakeRegistry()
                version = {"version": "1.0.0", "status": "draft" if action == "submit" else "reviewed"}
                if action == "publish":
                    version["publishPipelineInfo"] = {"status": "APPROVED"}
                remote.meta = {"name": "sample-skill", "scope": "PRIVATE", "editingVersion": "1.0.0", "versions": [version]}
                service = self.fresh_service("unknown-" + action, lambda *_: remote)
                service.invoke("configure", {"profile": self.profile, "expectedRevision": 0})
                plan = service.invoke("publish_plan", {"name": "sample-skill", "version": "1.0.0", "action": action})
                original_lifecycle = remote.lifecycle

                def lost_response(*args):
                    original_lifecycle(*args)
                    raise PluginError("result_unknown", "Synthetic lifecycle response lost")

                with patch.object(remote, "lifecycle", side_effect=lost_response):
                    unknown = service.invoke("apply", {"planId": plan["id"]})
                self.assertEqual(unknown["status"], "result_unknown")
                self.assert_rejected_without_save("apply", {"planId": plan["id"]}, service=service)
                result = service.invoke("reconcile", {"operationId": unknown["id"], "version": "1.0.0"})
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["result"]["status"], "online")
                self.assertTrue(result["reconciled"])
                self.assertEqual(service.invoke("apply", {"planId": plan["id"]})["id"], unknown["id"])
                self.assertEqual(remote.calls.count(action), 1)
                self.assertEqual(remote.calls, [action])

    def test_recovery_refuses_local_edits_and_does_not_touch_remote(self):
        installed = self.install()["result"]
        self.remote.content = skill("Remote update.")
        update = self.install()
        target = Path(installed["target"]) / "SKILL.md"
        local = skill("Local edit after installation.")["SKILL.md"]
        target.write_bytes(local)
        calls = list(self.remote.calls)
        self.assert_rejected_without_save("recover", {"operationId": update["id"]})
        self.assertEqual(target.read_bytes(), local)
        self.assertEqual(self.remote.calls, calls)
        self.assertEqual(self.call("inspect_operation", operationId=update["id"])["status"], "completed")
        self.assertEqual(self.call("status")["installations"][0]["lastOperationId"], update["id"])

    def test_reviewed_without_approved_review_cannot_publish(self):
        for review in (None, {"status": "REJECTED"}, {"status": "FAILED"}, {"status": "PENDING"},
                       {"status": "unknown"}, "invalid-json", {}, {"pipeline": [{"passed": True}]}):
            with self.subTest(review=review):
                version = {"version": "1.0.0", "status": "reviewed"}
                if review is not None:
                    version["publishPipelineInfo"] = review
                self.remote.meta = {"name": "sample-skill", "scope": "PRIVATE", "versions": [version]}
                with self.assertRaises(PluginError) as caught:
                    self.call("publish_plan", name="sample-skill", version="1.0.0", action="publish")
                expected = "review_rejected" if isinstance(review, dict) and review.get("status") in ("REJECTED", "FAILED") else "review_unverified"
                self.assertEqual(caught.exception.kind, expected)
                self.assertNotIn("publish", self.remote.calls)
        self.remote.meta["versions"][0]["publishPipelineInfo"] = json.dumps({"status": "APPROVED"})
        plan = self.call("publish_plan", name="sample-skill", version="1.0.0", action="publish")
        self.assertEqual(plan["currentStatus"], "reviewed")
        self.assertNotIn("publish", self.remote.calls)

    def test_approved_review_changed_before_apply_does_not_publish(self):
        self.remote.meta = {"name": "sample-skill", "scope": "PRIVATE", "versions": [
            {"version": "1.0.0", "status": "reviewed", "publishPipelineInfo": {"status": "APPROVED"}}]}
        plan = self.call("publish_plan", name="sample-skill", version="1.0.0", action="publish")
        self.remote.meta["versions"][0]["publishPipelineInfo"]["status"] = "REJECTED"
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error"], "conflict")
        self.assertNotIn("publish", self.remote.calls)

    def test_a2a_unknown_send_is_logged_without_automatic_resend(self):
        item = self.bind("agent")
        text = "synthetic-" + "private-agent-input-marker-2026"
        with patch("nacos_registry.remote.JsonRpc") as rpc:
            rpc.return_value.request.side_effect = PluginError("result_unknown", "Synthetic send response lost")
            result = self.call("agent_send", connectionId=item["id"], text=text)
            self.assertEqual(result["status"], "result_unknown")
            self.assertEqual(result["action"], "agent_send")
            rpc.return_value.request.assert_called_once()
            request = rpc.return_value.request.call_args
            self.assertEqual(request.args[0], "message/send")
            self.assertTrue(request.kwargs["mutation"])
            self.assertEqual(request.args[1]["message"]["parts"][0]["text"], text)
            self.assertEqual(result["inputDigest"], digest(text))
            self.assertNotIn(text, self.service.store.file.read_text())
            self.assertNotIn("taskHandle", result)
            self.assertEqual(self.call("status")["tasks"], [])
            self.assertEqual(self.call("inspect_operation", operationId=result["id"])["status"], "result_unknown")
            self.assert_rejected_without_save("reconcile", {"operationId": result["id"]}, "conflict")
            self.assertEqual(rpc.return_value.request.call_count, 1)
            self.assertEqual([op["id"] for op in self.call("status")["unfinishedOperations"]], [result["id"]])

    def test_a2a_cancel_unknown_is_reconciled_by_get_canceled_and_cannot_repeat(self):
        item = self.bind("agent")
        with patch("nacos_registry.remote.JsonRpc") as rpc:
            rpc.return_value.request.return_value = {"kind": "task", "id": "synthetic-task", "status": {"state": "working"}}
            sent = self.call("agent_send", connectionId=item["id"], text="Synthetic test input")
            handle = sent["taskHandle"]
            rpc.return_value.request.side_effect = PluginError("result_unknown", "Synthetic cancel response lost")
            canceled = self.call("agent_task", taskHandle=handle, action="cancel")
            self.assertEqual(canceled["status"], "result_unknown")
            task = self.call("status")["tasks"][0]
            self.assertTrue(task["cancelRequested"])
            self.assertEqual(task["status"], "working")
            count = rpc.return_value.request.call_count
            self.assert_rejected_without_save("agent_task", {"taskHandle": handle, "action": "cancel"})
            self.assertEqual(rpc.return_value.request.call_count, count)
            self.remote.endpoint = "changed.example.org"
            rpc.return_value.request.side_effect = None
            rpc.return_value.request.return_value = {"kind": "task", "id": "synthetic-task", "status": {"state": "working"}}
            self.call("agent_task", taskHandle=handle, action="get")
            self.assertEqual(self.call("inspect_operation", operationId=canceled["id"])["status"], "result_unknown")
            rpc.return_value.request.return_value["status"]["state"] = "canceled"
            result = self.call("agent_task", taskHandle=handle, action="get")
            self.assertEqual(result["result"]["status"]["state"], "canceled")
            reconciled = self.call("inspect_operation", operationId=canceled["id"])
            self.assertEqual(reconciled["status"], "completed")
            self.assertTrue(reconciled["reconciled"])
            self.assertEqual(reconciled["taskStatus"], "canceled")
            self.assertEqual(self.call("status")["tasks"][0]["status"], "canceled")
            count = rpc.return_value.request.call_count
            self.assert_rejected_without_save("agent_task", {"taskHandle": handle, "action": "cancel"})
            self.assertEqual(rpc.return_value.request.call_count, count)
            self.assertEqual([call.args[0] for call in rpc.return_value.request.call_args_list],
                             ["message/send", "tasks/cancel", "tasks/get", "tasks/get"])
            self.assertTrue(all(call.args[0] == "https://tools.example.org/rpc" for call in rpc.call_args_list))

    def test_target_change_with_aliases_of_same_credentials_requires_authorization(self):
        with patch.dict("os.environ", {"SYNTHETIC_USER": "user", "SYNTHETIC_PASSWORD": "password",
                                       "ALIAS_USER": "user", "ALIAS_PASSWORD": "password"}):
            self.configure_login()
            profile = {"namespaceId": "test", "clientUrl": "https://other.example.org/nacos",
                       "allowedOperations": self.profile["allowedOperations"], "adminMode": "shared",
                       "clientAuth": {"type": "login", "usernameEnv": "ALIAS_USER", "passwordEnv": "ALIAS_PASSWORD"}}
            revision = self.call("status")["configurationRevision"]
            self.assert_rejected_without_save("configure", {"profile": profile, "expectedRevision": revision}, "permission")
            saved = self.call("configure", profile=profile, authorizeCredentialReuse=True)
            self.assertEqual(saved["profile"]["clientAuth"], profile["clientAuth"])
            self.assertEqual(self.remote.calls, [])

    def test_downstream_aliases_cannot_reuse_registry_credential_values(self):
        with patch.dict("os.environ", {"REGISTRY_TOKEN": "synthetic-shared", "DOWNSTREAM_TOKEN": "synthetic-shared"}):
            self.call("configure", profile={"namespaceId": "test", "clientUrl": self.profile["clientUrl"],
                "allowedOperations": self.profile["allowedOperations"], "adminMode": "shared",
                "clientAuth": {"type": "token", "tokenEnv": "REGISTRY_TOKEN"}})
            for kind in ("mcp", "agent"):
                with self.subTest(kind=kind):
                    self.assert_rejected_without_save("connection_plan", {"resourceType": kind, "name": "test-" + kind,
                        "auth": {"type": "bearer", "tokenEnv": "DOWNSTREAM_TOKEN"}}, "validation")
            self.assertEqual(self.call("status")["connections"], [])

    def test_downstream_rotation_stales_plans_and_bindings_before_rpc(self):
        with patch.dict("os.environ", {"DOWNSTREAM_TOKEN": "first"}):
            auth = {"type": "bearer", "tokenEnv": "DOWNSTREAM_TOKEN"}
            mcp = self.bind(auth=auth)
            agent = self.bind("agent", auth=auth)
            pending = self.call("connection_plan", resourceType="mcp", name="pending-mcp", auth=auth)
            os.environ["DOWNSTREAM_TOKEN"] = "second"
            with patch("nacos_registry.remote.JsonRpc") as rpc:
                self.assert_rejected_without_save("mcp_probe", {"connectionId": mcp["id"]})
                self.assert_rejected_without_save("agent_send", {"connectionId": agent["id"], "text": "Synthetic input"})
                failed = self.call("apply", planId=pending["id"])
                self.assertEqual(failed["status"], "failed")
                self.assertEqual(failed["error"]["error"], "conflict")
                rpc.assert_not_called()
            refreshed = self.bind(auth=auth)
            with patch("nacos_registry.remote.JsonRpc") as rpc:
                rpc.return_value.initialize_mcp.return_value = {"capabilities": {"tools": {}}}
                rpc.return_value.request.return_value = {"tools": []}
                self.assertEqual(self.call("mcp_probe", connectionId=refreshed["id"])["transport"], "connected")

    def test_agent_task_rotation_requires_rebinding_exact_original_endpoint(self):
        with patch.dict("os.environ", {"DOWNSTREAM_TOKEN": "first"}):
            auth = {"type": "bearer", "tokenEnv": "DOWNSTREAM_TOKEN"}
            item = self.bind("agent", auth=auth)
            with patch("nacos_registry.remote.JsonRpc") as rpc:
                rpc.return_value.request.return_value = {"kind": "task", "id": "synthetic-task", "status": {"state": "working"}}
                handle = self.call("agent_send", connectionId=item["id"], text="Synthetic input")["taskHandle"]
                os.environ["DOWNSTREAM_TOKEN"] = "second"
                self.assert_rejected_without_save("agent_task", {"taskHandle": handle, "action": "get"})
                self.remote.endpoint = "new.example.org"
                self.bind("agent", auth=auth)
                self.assert_rejected_without_save("agent_task", {"taskHandle": handle, "action": "get"})
                self.assertEqual(rpc.return_value.request.call_count, 1)
                self.remote.endpoint = "tools.example.org"
                self.bind("agent", auth=auth)
                self.call("agent_task", taskHandle=handle, action="get")
                rpc.return_value.request.return_value["status"]["state"] = "canceled"
                self.call("agent_task", taskHandle=handle, action="cancel")
                self.assertEqual(self.call("status")["tasks"][0]["status"], "canceled")
                self.assertTrue(all(call.args[0] == "https://tools.example.org/rpc" for call in rpc.call_args_list))

    def test_concurrent_agent_binding_plans_do_not_overwrite(self):
        first = self.call("connection_plan", resourceType="agent", name="test-agent")
        second = self.call("connection_plan", resourceType="agent", name="test-agent",
                           auth={"type": "bearer", "tokenEnv": "DOWNSTREAM_TOKEN"})
        self.assertEqual(self.call("apply", planId=first["id"])["status"], "completed")
        failed = self.call("apply", planId=second["id"])
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["error"]["error"], "conflict")
        self.assertEqual(self.call("status")["connections"][0]["auth"], {"type": "none"})

    def test_ordinary_settings_preserve_owned_resources_choices_and_stale_writes(self):
        installed = self.install()["result"]
        mcp = self.bind()
        scan = self.call("scan")
        self.call("select", scanId=scan["id"], selections=[{"candidateId": scan["items"][0]["id"], "action": "ignore"}])
        self.call("onboarding", action="skip")
        pending = self.call("uninstall_plan", installationId=installed["id"])
        self.call("configure", profile={"namespaceId": "test", "clientUrl": self.profile["clientUrl"],
            "allowedOperations": self.profile["allowedOperations"], "displayName": "New display", "scanRoots": [str(self.source.parent)]})
        current = self.call("status")
        self.assertEqual(current["onboarding"], {"status": "skipped"})
        self.assertIsNone(current["scan"])
        self.assertEqual(current["installations"][0]["id"], installed["id"])
        self.assertEqual(current["connections"][0]["id"], mcp["id"])
        self.assertEqual(current["bindings"][0]["policy"], "ignore")
        self.assertEqual(current["installations"][0]["context"], digest(current["profile"]))
        self.assert_rejected_without_save("apply", {"planId": pending["id"]})
        self.assertEqual(self.call("scan")["items"][0]["selection"], "ignore")
        with patch("nacos_registry.remote.JsonRpc") as rpc:
            rpc.return_value.initialize_mcp.return_value = {"capabilities": {"tools": {}}}
            rpc.return_value.request.return_value = {"tools": []}
            self.assertEqual(self.call("mcp_probe", connectionId=mcp["id"])["transport"], "connected")

    def test_recovery_after_settings_change_keeps_current_installation_context(self):
        installed = self.install()["result"]
        self.remote.content = skill("Updated.")
        updated = self.install()
        self.call("configure", profile={"namespaceId": "test", "clientUrl": self.profile["clientUrl"],
            "allowedOperations": self.profile["allowedOperations"], "displayName": "New display"})
        calls = list(self.remote.calls)
        self.assertEqual(self.call("recover", operationId=updated["id"])["status"], "recovered")
        current = self.call("status")
        self.assertEqual(current["installations"][0]["context"], digest(current["profile"]))
        self.assertEqual((Path(installed["target"]) / "SKILL.md").read_bytes(), skill()["SKILL.md"])
        self.assertEqual(self.remote.calls, calls + ["download"])

    def test_unknown_upload_after_settings_change_reconciles_migrated_binding(self):
        self.upload_draft()
        (self.source / "SKILL.md").write_bytes(skill("Local update.")["SKILL.md"])
        plan = self.call("upload_plan", **self.upload_args())
        original = self.remote.upload

        def lost_response(*args):
            original(*args)
            raise PluginError("result_unknown", "Synthetic lost response")

        with patch.object(self.remote, "upload", side_effect=lost_response):
            unknown = self.call("apply", planId=plan["id"])
        self.assertEqual(unknown["status"], "result_unknown")
        self.call("configure", profile={"namespaceId": "test", "clientUrl": self.profile["clientUrl"],
            "allowedOperations": self.profile["allowedOperations"], "displayName": "New display"})
        self.assertEqual(self.call("reconcile", operationId=unknown["id"])["status"], "completed")
        current = self.call("status")
        self.assertEqual(len(current["bindings"]), 1)
        self.assertEqual(current["bindings"][0]["context"], digest(current["profile"]))
        self.assertEqual(self.call("scan")["items"][0]["selection"], "explicit")
        self.assertEqual(self.remote.calls.count("upload"), 2)

    def test_first_unknown_upload_reconciles_new_binding_after_settings_change(self):
        plan = self.call("upload_plan", **self.upload_args())
        original = self.remote.upload

        def lost_response(*args):
            original(*args)
            raise PluginError("result_unknown", "Synthetic lost response")

        with patch.object(self.remote, "upload", side_effect=lost_response):
            unknown = self.call("apply", planId=plan["id"])
        self.assertEqual(unknown["status"], "result_unknown")
        self.assertEqual(self.call("status")["bindings"], [])
        self.call("configure", profile={"namespaceId": "test", "clientUrl": self.profile["clientUrl"],
            "allowedOperations": self.profile["allowedOperations"], "displayName": "New display"})
        self.assertEqual(self.call("reconcile", operationId=unknown["id"])["status"], "completed")
        current = self.call("status")
        expected = digest({"path": str(self.source), "context": digest(current["profile"])})
        self.assertEqual([binding["id"] for binding in current["bindings"]], [expected])
        self.assertEqual(self.call("scan")["items"][0]["selection"], "explicit")
        self.assertEqual(self.remote.calls.count("upload"), 1)

    def test_configuration_rejects_whole_plugin_source_and_cache_roots(self):
        project = Path(__file__).resolve().parents[1]
        roots = [project, project / "src/nacos_qoder", project / "scripts", project / "skills",
                 self.root / "home/.qoder/plugins/cache/plugin", Path(project.anchor), self.root / "home"]
        for root in roots:
            with self.subTest(root=str(root)):
                self.assert_rejected_without_save("configure", {"profile": {**self.profile, "scanRoots": [str(root)]},
                    "expectedRevision": self.call("status")["configurationRevision"]}, "validation")

    def test_schema_forbids_unknown_fields_and_secret_values(self):
        for value in ({"expectedRevision": 1, "profile": {**self.profile, "password": "not-allowed"}},
                      {"expectedRevision": 1, "profile": {**self.profile, "clientAuth": {"type": "token", "token": "not-allowed"}}}):
            with self.assertRaises(PluginError) as caught:
                validate(value, DEFINITIONS["configure"][1])
            self.assertEqual(caught.exception.message, "Unknown tool argument")

    def test_setup_skill_requires_native_stepwise_guidance_and_safe_branches(self):
        instructions = (Path(__file__).resolve().parents[1] / "skills/nacos-setup/SKILL.md").read_text()
        for phrase in ("AskUserQuestion", "multiSelect: true", "不得一次列出全部字段",
                       "只问一个简短自由文本问题", "保存前", "取消或中止",
                       "credentialStatus", "不得调用 `nacos_diagnose`", "盘点", "跳过",
                       "不调用 configure", "分别询问需要的安装目录", "保留不调用 onboarding 或 scan",
                       "继续时复用当前 scan", "目录\n变更须重新审阅保存",
                       "非敏感自定义输入也必须优先调用 `AskUserQuestion`",
                       "没有可信候选不等于原生问答不可用", "不在 options 中重复添加 Other",
                       "不得虚构 URL", "不得要求先选“输入”再到聊天填写",
                       "实际调用明确返回不支持/不可用", "先说明降级原因",
                       "用户拒绝或取消调用不是", "工具可用时恢复原生问答",
                       "不得仅输出“请提供 URL”后等待聊天回复"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, instructions)
        self.assertNotIn("若当前 `AskUserQuestion` 的 Other 输入适用，可用 Other", instructions)
        self.assertIn("环境变量名", instructions)
        self.assertIn("不得询问、读取或回显秘密值", instructions)
        for phrase in ("默认命名空间（ID `public`）", "系统钥匙串（推荐）", "环境变量（高级备用）",
                       "无需命令行或重启", "nacos_credentials", "不回填 credentialRef", "cleanupPending"):
            self.assertIn(phrase, instructions)
        recovery = instructions.split("3. 保存返回 configured/unverified", 1)[1].split("4. 凭据就绪后", 1)[0]
        for phrase in ("重新核对最新 status 的 `credentialStorage.available`",
                       "只有为 true 时才提供“打开安全输入”或\n     “改用系统钥匙串”",
                       "安全入口不可用时说明原因，不调用 credentials enter，不自动改用环境变量",
                       "修改认证仍须明确选择来源", "始终提供“设置后再检查”“暂时结束”"):
            self.assertIn(phrase, recovery)
        self.assertNotIn("公共命名空间", instructions)
        self.assertNotIn("推荐环境变量名", instructions)
        example = json.loads(instructions.split("```json\n", 1)[1].split("\n```", 1)[0])
        self.assertEqual(set(example), {"questions"})
        self.assertEqual(len(example["questions"]), 1)
        question = example["questions"][0]
        self.assertIn("其他", question["question"])
        self.assertEqual(question["header"], "Client URL")
        self.assertEqual([option["label"] for option in question["options"]], ["稍后配置", "取消初始化"])
        self.assertTrue(all("不保存未确认配置" in option["description"] for option in question["options"]))
        self.assertNotIn("http://", json.dumps(example))
        self.assertNotIn("https://", json.dumps(example))
        downstream = json.loads(instructions.split("```json\n")[2].split("\n```", 1)[0])
        self.assertEqual(set(downstream), {"questions"})
        self.assertEqual(len(downstream["questions"]), 1)
        question = downstream["questions"][0]
        self.assertEqual(question["header"], "下游用途")
        self.assertIs(question["multiSelect"], False)
        self.assertEqual([option["label"] for option in question["options"]],
                         ["不使用", "接入 MCP", "调用远端 Agent", "都需要"])
        self.assertIn("MCP", question["question"])
        self.assertIn("Agent", question["question"])
        self.assertIn("MCP 和远端 Agent", question["options"][-1]["description"])
        self.assertIn("不包含未来新增能力", question["options"][-1]["description"])
        for phrase in ("不得省略“都需要”", "下游用途使用单选", "不授权未来新增能力",
                       "增加 `install`、`call`，不额外授予 `develop` 或\n   `publish`",
                       "合并已选 Skill 用途后去重", "也不自动注册 MCP 或调用 Agent"):
            self.assertIn(phrase, instructions)
        self.assertLessEqual(len(instructions.splitlines()), 500)


class LocalHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        home = Path(self.temp.name).resolve() / "home"
        self.enterContext(patch.dict("os.environ", {"HOME": str(home)}, clear=True))
        self.enterContext(patch("nacos_qoder.host.Path.home", return_value=home))
        self.enterContext(patch("nacos_qoder.host.socket.gethostname", return_value="synthetic-http-host"))
        self.enterContext(patch("nacos_qoder.host.getpass.getuser", return_value="synthetic-http-user"))

    def test_qoder_registry_search_and_exact_skill_install_over_http(self):
        calls = []
        zipped = package.pack(skill())

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                calls.append(self.path)
                self.send_response(200)
                if self.path.startswith("/nacos/v3/client/ai/skills?"):
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("X-Nacos-Skill-Resolved-Version", "1.0.0")
                    self.end_headers()
                    self.wfile.write(zipped)
                else:
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"code": 0, "data": {"items": [], "nextCursor": "opaque"}}).encode())

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                service = Service(Store(root / "state"))
                url = f"http://127.0.0.1:{server.server_port}/nacos"
                profile = {"id": "local-test", "identityId": "tester", "namespaceId": "test",
                           "clientUrl": url, "adminUrl": url, "allowedOperations": ["read", "install"],
                           "installRoots": [str(root / ".qoder/skills")]}
                service.invoke("configure", {"profile": profile, "expectedRevision": 0})
                self.assertEqual(service.invoke("diagnose")["clientRead"], "passed")
                self.assertEqual(service.invoke("search", {"query": "sample"})["result"]["nextCursor"], "opaque")
                plan = service.invoke("install_plan", {"name": "sample-skill", "version": "1.0.0", "installRoot": profile["installRoots"][0]})
                result = service.invoke("apply", {"planId": plan["id"]})
                self.assertEqual(result["status"], "completed")
                self.assertEqual((root / ".qoder/skills/sample-skill/SKILL.md").read_bytes(), skill()["SKILL.md"])
                self.assertTrue(all("namespaceId=test" in call for call in calls))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
