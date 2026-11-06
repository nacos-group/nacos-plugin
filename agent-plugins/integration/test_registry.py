# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Service-level integration against the owned Nacos instance; no Registry/HTTP mocks."""
import copy
import json
import os
from pathlib import Path
import sys
import time
import unittest
import uuid
from urllib import error, parse, request

from downstream import Peers, ResponseLossProxy
from nacos_registry import package
from nacos_registry.errors import PluginError
from nacos_registry.registry import Registry
from nacos_registry.store import Store
if os.environ["NACOS_IT_ADAPTER"] == "codex":
    from nacos_registry.service import Service
else:
    from nacos_qoder.service import Service

AUTH = os.environ["NACOS_IT_AUTH"]
ROOT = Path(os.environ["NACOS_IT_ROOT"])
DOWNSTREAM_AUTH = {"type": "bearer", "tokenEnv": "NACOS_IT_DOWNSTREAM_TOKEN"}


def poll(read, ready, description, timeout=40):
    deadline = time.monotonic() + timeout
    while True:
        value = read()
        if ready(value):
            return value
        if time.monotonic() >= deadline:
            raise AssertionError("Timed out waiting for " + description)
        time.sleep(0.5)


class RegistryIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ROOT.mkdir(parents=True)
        cls.namespace = "plugin-it-" + uuid.uuid4().hex[:12]
        auth = {"type": "none"} if AUTH == "disabled" else {
            "type": "login", "usernameEnv": "NACOS_IT_USER", "passwordEnv": "NACOS_IT_PASSWORD"}
        cls.base = {"id": "integration", "identityId": "integration-user", "namespaceId": cls.namespace,
                    "clientUrl": os.environ["NACOS_IT_URL"], "adminUrl": os.environ["NACOS_IT_URL"],
                    "clientAuth": auth, "adminAuth": auth,
                    "allowedOperations": ["read", "develop", "publish", "install", "call"]}
        cls.registry = Registry(cls.base)
        cls.registry.request("admin", "/v3/admin/core/namespace", {
            "namespaceId": cls.namespace, "namespaceName": cls.namespace, "namespaceDesc": "Disposable plugin IT"}, "POST")
        cls.peers = Peers()
        cls.addClassCleanup(cls.peers.close)

    def setUp(self):
        self.root = ROOT / self._testMethodName
        self.source = self.root / "source"
        self.source.mkdir(parents=True)
        self.profile = copy.deepcopy(self.base)
        self.profile.update(scanRoots=[str(self.source)], installRoots=[str(self.root / "installed")])
        if os.environ["NACOS_IT_ADAPTER"] == "codex":
            self.profile["codexConfig"] = str(self.root / "host/config.toml")
        self.service = Service(Store(self.root / "state"))
        self.configure(self.profile)

    def call(self, method, **args):
        return self.service.invoke(method, args)

    def configure(self, profile, authorize_reuse=False):
        args = {"profile": profile}
        if os.environ["NACOS_IT_ADAPTER"] == "qoder":
            args["expectedRevision"] = self.call("status")["configurationRevision"]
            args["authorizeCredentialReuse"] = authorize_reuse
        return self.call("configure", **args)

    def apply(self, plan):
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "completed", result)
        return result

    def skill(self, version="1.0.0", name=None, body="Synthetic integration content."):
        name = name or "plugin-it-" + uuid.uuid4().hex[:12]
        path = self.source / name
        path.mkdir(exist_ok=True)
        (path / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Synthetic integration capability.\nversion: {version}\n---\n\n{body}\n")
        (path / "guide.txt").write_text("Test reference")
        return name, path

    def plan_upload(self, name, **options):
        scan = self.call("scan")
        item = next(item for item in scan["items"] if item.get("name") == name)
        return self.call("upload_plan", scanId=scan["id"], candidateId=item["id"], **options)

    def draft(self, **kwargs):
        name, path = self.skill(**kwargs)
        uploaded = self.apply(self.plan_upload(name))
        self.assertEqual(uploaded["result"]["status"], "draft")
        return name, path

    def version(self, name, version="1.0.0"):
        return next(x for x in self.registry.skill_meta(name)["versions"] if x["version"] == version)

    def publish(self, name, version="1.0.0"):
        self.apply(self.call("publish_plan", name=name, version=version, action="submit"))
        selected = poll(lambda: self.version(name, version),
                        lambda x: x["status"] == "reviewed", "real pipeline completion")
        self.assertEqual(json.loads(selected["publishPipelineInfo"])["status"], "APPROVED")
        result = self.apply(self.call("publish_plan", name=name, version=version, action="publish"))
        self.assertEqual(result["result"]["status"], "online")
        self.assertTrue(result["result"]["consumerVerified"])
        return result

    def online_skill(self):
        name, path = self.draft()
        self.publish(name)
        return name, path

    def install(self, name, version=None, **options):
        return self.call("install_plan", name=name, version=version,
                         installRoot=self.profile["installRoots"][0], **options)

    def expect_error(self, kinds, method, **args):
        with self.assertRaises(PluginError) as caught:
            self.call(method, **args)
        self.assertIn(caught.exception.kind, kinds)

    def test_authentication_and_diagnosis(self):
        self.assertEqual(self.call("diagnose")["clientRead"], "passed")
        if AUTH == "enabled":
            token = self.registry.headers("client")["accessToken"]
            os.environ["NACOS_IT_TOKEN"] = token
            profile = copy.deepcopy(self.profile)
            profile["clientAuth"] = profile["adminAuth"] = {"type": "token", "tokenEnv": "NACOS_IT_TOKEN"}
            self.configure(profile)
            self.assertEqual(self.call("diagnose")["clientRead"], "passed")
            os.environ["NACOS_IT_BAD_PASSWORD"] = "synthetic-invalid-password"
            profile["clientAuth"] = {"type": "login", "usernameEnv": "NACOS_IT_USER",
                                     "passwordEnv": "NACOS_IT_BAD_PASSWORD"}
            self.configure(profile)
            self.expect_error({"authentication"}, "diagnose")
            profile["clientAuth"] = {"type": "none"}
            self.configure(profile)
            self.expect_error({"authentication", "permission"}, "diagnose")
        else:
            self.assertEqual(self.profile["clientAuth"]["type"], "none")

    def test_scan_preview_upload_binding_and_owned_list(self):
        name, path = self.skill()
        scan = self.call("scan")
        item = next(x for x in scan["items"] if x["name"] == name)
        args = {"scanId": scan["id"], "candidateId": item["id"]}
        with self.assertRaises(PluginError):
            self.registry.skill_meta(name)
        preview = self.call("upload_preview", **args)
        self.assertEqual(preview["name"], name)
        uploaded = self.apply(self.call("upload_plan", **args, expectedContentHash=preview["contentHash"]))
        self.assertEqual(self.call("apply", planId=uploaded["planId"])["id"], uploaded["id"])
        self.assertEqual(self.version(name)["status"], "draft")
        self.assertIn(b"Synthetic integration content.", package.unpack(self.registry.draft_zip(name, "1.0.0"))["SKILL.md"])
        # A separate state store must explicitly bind an existing name and authorize overwrite.
        self.service = Service(Store(self.root / "other-state"))
        self.configure(self.profile)
        self.expect_error({"conflict"}, "upload_plan", **self._scan_args(name))
        self.expect_error({"conflict"}, "upload_plan", **self._scan_args(name), bindExisting=True)
        self.apply(self.plan_upload(name, bindExisting=True, overwriteDraft=True))
        if AUTH == "enabled":
            owned = self.call("my_skills", query=name)
            self.assertEqual([x["name"] for x in owned["items"]], [name])

    def _scan_args(self, name):
        scan = self.call("scan")
        item = next(x for x in scan["items"] if x.get("name") == name)
        return {"scanId": scan["id"], "candidateId": item["id"]}

    def test_fix01_observed_download_statistics_and_unchanged_content(self):
        name, _ = self.draft()
        before = self.version(name)
        plan = self.plan_upload(name, overwriteDraft=True)
        other = Registry(copy.deepcopy(self.base))
        for _ in range(3):
            other.draft_zip(name, "1.0.0")
        after = poll(lambda: self.version(name),
                     lambda x: x["downloadCount"] > before["downloadCount"] and x["updateTime"] != before["updateTime"],
                     "persisted download count AND version updateTime")
        self.assertEqual(after["status"], before["status"])
        self.assertEqual(package.hashes(package.unpack(other.draft_zip(name, "1.0.0"))), plan["draftHashes"])
        self.service = Service(Store(self.root / "state"))
        self.apply(plan)

    def test_upload_real_content_visibility_and_lifecycle_conflicts(self):
        for change in ("local", "remote", "scope", "submit"):
            with self.subTest(change=change):
                name, path = self.draft()
                plan = self.plan_upload(name, overwriteDraft=True)
                if change == "local":
                    (path / "guide.txt").write_text("Unreviewed local edit")
                elif change == "remote":
                    content = package.unpack(self.registry.draft_zip(name, "1.0.0"))
                    content["guide.txt"] = b"Concurrent remote edit"
                    self.registry.upload(package.pack(content), "OVERWRITE_DRAFT", "1.0.0", "Concurrent test edit")
                elif change == "scope":
                    scope = self.registry.skill_meta(name)["scope"]
                    self.registry.request("admin", "/v3/admin/ai/skills/scope",
                                          {"skillName": name, "scope": "PUBLIC" if scope == "PRIVATE" else "PRIVATE"}, "PUT")
                else:
                    self.registry.lifecycle(name, "1.0.0", "submit")
                    poll(lambda: self.version(name), lambda x: x["status"] != "draft", "lifecycle transition")
                remote_before = package.hashes(package.unpack(self.registry.draft_zip(name, "1.0.0")))
                result = self.call("apply", planId=plan["id"])
                self.assertEqual(result["error"]["error"], "conflict", result)
                self.assertEqual(package.hashes(package.unpack(self.registry.draft_zip(name, "1.0.0"))), remote_before)

    def test_review_approval_publish_and_rejection(self):
        name, _ = self.draft()
        self.expect_error({"conflict"}, "publish_plan", name=name, version="1.0.0", action="publish")
        self.publish(name)
        rejected, _ = self.draft(body="IT_REJECT synthetic scanner test marker")
        self.apply(self.call("publish_plan", name=rejected, version="1.0.0", action="submit"))
        selected = poll(lambda: self.version(rejected), lambda x: x["status"] == "reviewed", "rejected review")
        self.assertEqual(json.loads(selected["publishPipelineInfo"])["status"], "REJECTED")
        self.expect_error({"review_rejected"}, "publish_plan", name=rejected, version="1.0.0", action="publish")
        self.assertNotEqual(self.version(rejected)["status"], "online")

    def test_install_update_local_conflicts_uninstall_and_recovery(self):
        name, _ = self.online_skill()
        installed = self.apply(self.install(name, "1.0.0"))["result"]
        target = Path(installed["target"])
        original = package.disk_hashes(target)
        self.skill(name=name, version="1.0.1", body="Second version")
        self.apply(self.plan_upload(name))
        self.publish(name, "1.0.1")
        (target / "guide.txt").write_text("User edit")
        self.expect_error({"conflict"}, "install_plan", name=name, installRoot=self.profile["installRoots"][0])
        self.expect_error({"conflict"}, "uninstall_plan", installationId=installed["id"])
        self.assertEqual((target / "guide.txt").read_text(), "User edit")
        (target / "guide.txt").write_text("Test reference")
        self.assertEqual(package.disk_hashes(target), original)
        updated = self.apply(self.install(name, "1.0.1"))["result"]
        self.assertIn("Second version", (target / "SKILL.md").read_text())
        self.service = Service(Store(self.root / "state"))
        self.assertEqual(self.call("status")["installations"][0]["version"], "1.0.1")
        verified = self.call("verify_skill", installationId=updated["id"])
        self.assertEqual(verified["files"], "verified")
        self.assertEqual(verified["remote"], "readable")
        self.assertEqual(verified["loadState"], "pending_host_verification")
        removed = self.apply(self.call("uninstall_plan", installationId=updated["id"]))
        self.assertFalse(target.exists())
        self.call("recover", operationId=removed["id"])
        self.assertEqual(package.disk_hashes(target), updated["hashes"])
        self.assertEqual(self.version(name, "1.0.1")["status"], "online")

    def test_install_rechecks_remote_availability_before_writing(self):
        name, _ = self.online_skill()
        plan = self.install(name)
        self.registry.request("admin", "/v3/admin/ai/skills/offline", {"skillName": name, "version": "1.0.0"}, "POST")
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "failed", result)
        self.assertFalse(Path(plan["target"]).exists())

    def test_preview_and_reuse_policy_persistence(self):
        name, _ = self.online_skill()
        preview = self.call("preview_skill", name=name)
        self.assertIn("Synthetic integration content.", preview["content"])
        self.assertFalse(preview["installed"])
        self.assertFalse(Path(self.profile["installRoots"][0]).exists())
        self.expect_error({"permission"}, "install_plan", name=name,
                          installRoot=self.profile["installRoots"][0], discoveryReuse="automatic")
        self.call("configure_discovery", installPolicy="auto")
        plan = self.install(name, discoveryReuse="automatic")
        self.call("configure_discovery", installPolicy="never")
        self.expect_error({"permission"}, "apply", planId=plan["id"])
        self.service = Service(Store(self.root / "state"))
        self.assertEqual(self.call("status")["discovery"]["installPolicy"], "never")
        self.apply(self.install(name))  # Explicit installation remains independent.

    def test_profile_change_and_read_only_scope_invalidate_writes(self):
        name, _ = self.draft()
        plan = self.plan_upload(name, overwriteDraft=True)
        profile = copy.deepcopy(self.profile)
        profile["identityId"] = "another-identity"
        self.configure(profile)
        self.expect_error({"conflict"}, "apply", planId=plan["id"])
        profile["allowedOperations"] = ["read"]
        self.configure(profile)
        self.assertEqual(self.call("diagnose")["clientRead"], "passed")
        self.expect_error({"permission"}, "upload_plan", **self._scan_args(name))

    def test_lost_upload_response_reconciles_without_repeating_write(self):
        proxy = ResponseLossProxy(self.base["adminUrl"])
        self.addCleanup(proxy.close)
        profile = copy.deepcopy(self.profile)
        profile["adminUrl"] = proxy.url  # Client/Admin now use separate origins.
        self.configure(profile, authorize_reuse=True)
        name, _ = self.skill()
        plan = self.plan_upload(name)
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "result_unknown", result)
        self.assertEqual(self.version(name)["status"], "draft")
        self.expect_error({"conflict"}, "apply", planId=plan["id"])
        reconciled = self.call("reconcile", operationId=result["id"])
        self.assertEqual(reconciled["status"], "completed", reconciled)
        self.assertEqual(proxy.uploads, 1)

    def register_mcp(self):
        name = "plugin-it-" + uuid.uuid4().hex[:12]
        spec = {"name": name, "protocol": "mcp-streamable", "frontProtocol": "mcp-streamable",
                "description": "Synthetic integration capability.", "enabled": True,
                "versionDetail": {"version": "1.0.0"},
                "remoteServerConfig": {"exportPath": "/mcp", "frontEndpointConfigList": [{
                    "protocol": "http", "endpointType": "DIRECT",
                    "endpointData": f"127.0.0.1:{self.peers.port}", "path": "/mcp"}]}}
        self.registry.request("admin", "/v3/admin/ai/mcp", {
            "mcpName": name, "serverSpecification": json.dumps(spec),
            "endpointSpecification": json.dumps({"type": "DIRECT", "data": {
                "address": "127.0.0.1", "port": str(self.peers.port)}})}, "POST")
        return name

    def register_agent(self):
        name = "plugin-it-" + uuid.uuid4().hex[:12]
        interface = {"protocol": "a2a", "protocolVersion": "0.3.0", "descriptorMediaType": "application/json",
                     "nativeDescriptor": {"name": name, "version": "1.0.0", "protocolVersion": "0.3.0",
                                          "preferredTransport": "JSONRPC", "url": self.peers.url + "/agent"},
                     "endpointSourceOrder": ["DECLARED", "RUNTIME"],
                     "endpointSets": [{"source": "DECLARED", "endpoints": [{
                         "uri": self.peers.url + "/agent", "transport": "JSONRPC"}]}]}
        self.seed("/v3/admin/ai/agents/draft", {
            "agentName": name, "displayName": name, "description": "Synthetic integration capability.",
            "version": "1.0.0", "callInterfaces": json.dumps([interface])})
        self.registry.request("admin", "/v3/admin/ai/agents/force-publish",
                              {"agentName": name, "version": "1.0.0"}, "POST")
        return name

    def seed(self, route, fields):
        # Setup errors may include the synthetic fixture's validation details; never log login responses.
        fields = {"namespaceId": self.namespace, **fields}
        req = request.Request(self.base["adminUrl"] + route, data=parse.urlencode(fields).encode(),
                              headers=self.registry.headers("admin"))
        try:
            with request.urlopen(req, timeout=20) as response:
                value = json.load(response)
        except error.HTTPError as exc:
            self.fail(f"Fixture {route}: HTTP {exc.code}: {exc.read(4096).decode(errors='replace')}")
        self.assertEqual(value["code"], 0, value)
        return value["data"]

    def test_search_types_pagination_and_namespace_isolation(self):
        skill, _ = self.online_skill()
        mcp, agent = self.register_mcp(), self.register_agent()
        expected = {("skill", skill), ("mcp", mcp), ("agent", agent)}
        poll(lambda: self.call("search", query="plugin-it-", limit=100)["result"]["items"],
             lambda rows: expected <= {(x["resourceType"], x["resourceName"]) for x in rows}, "search index")
        found, cursors, cursor = set(), set(), None
        for _ in range(100):
            page = self.call("search", query="plugin-it-", limit=1, cursor=cursor)["result"]
            for item in page["items"]:
                key = (item["resourceType"], item["resourceName"])
                self.assertNotIn(key, found)
                found.add(key)
            cursor = page.get("nextCursor")
            if not cursor:
                break
            self.assertNotIn(cursor, cursors)
            cursors.add(cursor)
        else:
            self.fail("Search pagination did not terminate")
        self.assertTrue(expected <= found)
        only = self.call("search", query=skill, resourceTypes=["skill"])["result"]["items"]
        self.assertEqual({(x["resourceType"], x["resourceName"]) for x in only}, {("skill", skill)})
        # A separate real namespace, not a changed local label.
        empty = "plugin-it-" + uuid.uuid4().hex[:12]
        self.registry.request("admin", "/v3/admin/core/namespace",
                              {"namespaceId": empty, "namespaceName": empty}, "POST")
        profile = copy.deepcopy(self.profile)
        profile["namespaceId"] = empty
        self.configure(profile)
        self.assertEqual(self.call("search", query=skill)["result"]["items"], [])

    def test_mcp_discovery_trial_binding_probe_disconnect_and_auth(self):
        name = self.register_mcp()
        found = self.call("discover", resourceType="mcp", name=name)
        self.assertEqual(found["endpoints"][0]["url"], self.peers.url + "/mcp")
        self.expect_error({"authentication"}, "mcp_trial", name=name)
        result = self.call("mcp_trial", name=name, auth=DOWNSTREAM_AUTH, tool="echo",
                           arguments={"text": "synthetic echo"})
        self.assertEqual(result["realUse"], "completed", result)
        self.assertEqual(result["result"]["content"][0]["text"], "synthetic echo")
        self.assertFalse(self.call("status")["connections"])
        bound = self.apply(self.call("connection_plan", resourceType="mcp", name=name, auth=DOWNSTREAM_AUTH))["result"]
        probe = self.call("mcp_probe", connectionId=bound["id"])
        self.assertEqual(probe["tools"][0]["name"], "echo")
        self.assertNotEqual(probe.get("hostLoaded"), True)
        self.apply(self.call("disconnect_plan", connectionId=bound["id"]))
        self.assertFalse(self.call("status")["connections"])
        self.assertTrue(self.registry.discover("mcp", name))

    def test_agent_discovery_trial_binding_query_cancel_and_disconnect(self):
        name = self.register_agent()
        found = self.call("discover", resourceType="agent", name=name)
        self.assertEqual(found["endpoints"][0]["url"], self.peers.url + "/agent")
        failed = self.call("agent_trial", name=name, text="synthetic task")
        self.assertEqual(failed["status"], "failed", failed)
        self.assertEqual(failed["error"]["error"], "authentication")
        trial = self.call("agent_trial", name=name, text="synthetic task", auth=DOWNSTREAM_AUTH)
        self.assertFalse(self.call("status")["connections"])
        self.assertEqual(self.call("agent_task", taskHandle=trial["taskHandle"], action="get")["result"]["status"]["state"], "working")
        self.assertEqual(self.call("agent_task", taskHandle=trial["taskHandle"], action="cancel")["result"]["status"]["state"], "canceled")
        bound = self.apply(self.call("connection_plan", resourceType="agent", name=name, auth=DOWNSTREAM_AUTH))["result"]
        sent = self.call("agent_send", connectionId=bound["id"], text="another synthetic task")
        self.service = Service(Store(self.root / "state"))
        self.assertEqual(self.call("agent_task", taskHandle=sent["taskHandle"])["result"]["status"]["state"], "working")
        self.apply(self.call("disconnect_plan", connectionId=bound["id"]))
        self.assertFalse(self.call("status")["connections"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RegistryIntegration)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"adapter": os.environ["NACOS_IT_ADAPTER"], "auth": AUTH,
              "tests": result.testsRun, "failures": [t.id() for t, _ in result.failures],
              "errors": [t.id() for t, _ in result.errors], "skipped": [t.id() for t, _ in result.skipped],
              "successful": result.wasSuccessful() and not result.skipped}
    Path(os.environ["NACOS_IT_REPORT"]).write_text(json.dumps(report, indent=2) + "\n")
    sys.exit(0 if report["successful"] else 1)
