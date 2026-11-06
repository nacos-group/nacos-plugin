# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""FIX01: exercise plans and writes against ZIP reads that change server statistics."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nacos_registry import package
from nacos_registry.store import Store
from nacos_registry.service import Service


class ReadingRegistry:
    def __init__(self):
        self.content = {"SKILL.md": b"---\nname: sample-skill\ndescription: Synthetic test.\nversion: 1.0.0\n---\n\nOriginal content.\n"}
        self.meta = {
            "name": "sample-skill", "scope": "PRIVATE", "enable": True, "owner": "test-user",
            "editingVersion": "1.0.0", "reviewingVersion": None, "labels": {},
            "downloadCount": 0, "updateTime": 100,
            "versions": [{"version": "1.0.0", "status": "draft", "createTime": 1,
                          "updateTime": 100, "downloadCount": 0, "commitMsg": "Initial draft",
                          "publishPipelineInfo": None}],
        }
        self.reads = 0
        self.writes = []

    def skill_meta(self, name):
        return copy.deepcopy(self.meta)

    def draft_zip(self, name, version):
        selected = next(x for x in self.meta["versions"] if x["version"] == version)
        # Nacos persists download counts together with gmt_modified; metadata exposes it as updateTime.
        self.reads += 1
        for target in (self.meta, selected):
            target["downloadCount"] += 1
            target["updateTime"] += 1
        return package.pack(self.content)

    def download(self, name, version=None, label=None):
        version = version or "1.0.0"
        return version, "synthetic-md5", self.draft_zip(name, version)

    def precheck(self, data):
        editing = self.meta["editingVersion"]
        return [{"skillName": "sample-skill", "precheckCode": "DRAFT_EXISTS" if editing else "READY",
                 "editingVersion": editing, "targetVersion": editing or "1.0.1"}]

    def upload(self, data, action, version, message):
        self.writes.append(("upload", action, version))
        self.content = package.unpack(data)
        self.meta["editingVersion"] = version
        return "sample-skill"

    def lifecycle(self, name, version, action):
        self.writes.append((action, version))
        self.meta["editingVersion"] = None
        self.meta["versions"][0]["status"] = "online"


class UploadConflictTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.source = self.root / "skills/sample-skill"
        self.source.mkdir(parents=True)
        self.remote = ReadingRegistry()
        (self.source / "SKILL.md").write_bytes(self.remote.content["SKILL.md"])
        self.service = Service(Store(self.root / "state"), lambda *_: self.remote)
        profile = {"id": "test", "identityId": "test-user", "namespaceId": "test",
                   "clientUrl": "https://registry.example.org/nacos", "adminUrl": "https://registry.example.org/nacos",
                   "allowedOperations": ["read", "develop", "publish"],
                   "scanRoots": [str(self.source.parent)], "installRoots": []}
        self.call("configure", profile=profile)
        scan = self.call("scan")
        self.candidate = {"scanId": scan["id"], "candidateId": scan["items"][0]["id"]}

    def call(self, method, **arguments):
        return self.service.invoke(method, arguments)

    def upload_plan(self):
        return self.call("upload_plan", **self.candidate, bindExisting=True, overwriteDraft=True)

    def lifecycle_plan(self, action):
        self.remote.meta["versions"][0].update(
            status="reviewed" if action == "publish" else "draft",
            publishPipelineInfo='{"status":"APPROVED"}' if action == "publish" else None)
        return self.call("publish_plan", name="sample-skill", version="1.0.0", action=action)

    def assert_conflict(self, plan):
        before = copy.deepcopy(self.remote.content)
        writes = list(self.remote.writes)
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "failed", result)
        self.assertEqual(result["error"]["error"], "conflict")
        self.assertEqual(self.remote.writes, writes)
        self.assertEqual(self.remote.content, before)

    def test_upload_plan_own_zip_read_does_not_conflict(self):
        plan = self.upload_plan()
        self.assertEqual(self.remote.reads, 1)
        self.assertEqual(plan["action"], "OVERWRITE_DRAFT")
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "completed", result)
        self.assertEqual(self.remote.writes, [("upload", "OVERWRITE_DRAFT", "1.0.0")])

    def test_bound_upload_survives_other_readers_and_service_restart(self):
        first = self.call("apply", planId=self.upload_plan()["id"])
        self.assertEqual(first["status"], "completed", first)
        (self.source / "SKILL.md").write_bytes(self.remote.content["SKILL.md"] + b"Local edit.\n")
        plan = self.upload_plan()
        before = copy.deepcopy(self.remote.meta)
        # Deterministic interleaving: other clients read after planning and before applying.
        for _ in range(3):
            self.remote.download("sample-skill", "1.0.0")
        self.assertNotEqual(before, self.remote.meta)
        self.service = Service(Store(self.root / "state"), lambda *_: self.remote)
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "completed", result)
        self.assertEqual(self.remote.content["SKILL.md"], (self.source / "SKILL.md").read_bytes())
        self.assertEqual(len(self.remote.writes), 2)

    def test_upload_rejects_changed_draft_even_when_metadata_is_unchanged(self):
        plan = self.upload_plan()
        self.remote.content["reference.txt"] = b"Concurrent remote edit"
        self.assert_conflict(plan)

    def test_upload_rejects_changed_local_files(self):
        plan = self.upload_plan()
        (self.source / "SKILL.md").write_bytes(self.remote.content["SKILL.md"] + b"Changed after planning\n")
        self.assert_conflict(plan)

    def test_upload_accepts_legacy_baseline_with_version_timestamp(self):
        plan = self.upload_plan()
        # 0.1.0 stored the version timestamp, but not its download count, in the baseline.
        plan["remoteBaseline"]["versions"][0]["updateTime"] = 100
        self.service.store.save()
        self.remote.download("sample-skill", "1.0.0")
        self.service = Service(Store(self.root / "state"), lambda *_: self.remote)
        result = self.call("apply", planId=plan["id"])
        self.assertEqual(result["status"], "completed", result)

    def test_lifecycle_own_and_concurrent_reads_do_not_conflict(self):
        for action in ("submit", "publish"):
            with self.subTest(action=action):
                plan = self.lifecycle_plan(action)
                self.remote.download("sample-skill", "1.0.0")
                result = self.call("apply", planId=plan["id"])
                self.assertEqual(result["status"], "completed", result)
                self.assertEqual(self.remote.writes[-1], (action, "1.0.0"))

    def test_lifecycle_rejects_changed_content_even_when_metadata_is_unchanged(self):
        for action in ("submit", "publish"):
            with self.subTest(action=action):
                plan = self.lifecycle_plan(action)
                self.remote.content["reference.txt"] = action.encode()
                self.assert_conflict(plan)

    def test_lifecycle_requires_fresh_plan_if_legacy_plan_has_no_content_baseline(self):
        plan = self.lifecycle_plan("submit")
        plan.pop("contentHashes", None)
        plan["remoteBaseline"]["versions"][0]["updateTime"] = 100
        self.service.store.save()
        self.assert_conflict(plan)

    def test_lifecycle_rechecks_governance_after_reading_content(self):
        for action in ("submit", "publish"):
            with self.subTest(action=action):
                plan = self.lifecycle_plan(action)
                original = self.remote.draft_zip

                def read_then_reject(*args):
                    data = original(*args)
                    self.remote.meta["versions"][0]["publishPipelineInfo"] = '{"status":"REJECTED"}'
                    return data

                with patch.object(self.remote, "draft_zip", side_effect=read_then_reject):
                    self.assert_conflict(plan)

    def test_governance_changes_still_block_upload_submit_and_publish(self):
        changes = {
            "scope": lambda m: m.update(scope="PUBLIC"),
            "enabled": lambda m: m.update(enable=False),
            "owner": lambda m: m.update(owner="another-user"),
            "editing": lambda m: m.update(editingVersion="2.0.0"),
            "reviewing": lambda m: m.update(reviewingVersion="1.0.0"),
            "latest": lambda m: m.update(labels={"latest": "2.0.0"}),
            "status": lambda m: m["versions"][0].update(status="offline"),
            "review": lambda m: m["versions"][0].update(publishPipelineInfo='{"status":"REJECTED"}'),
            "commit": lambda m: m["versions"][0].update(commitMsg="Edited"),
            "new_version": lambda m: m["versions"].append({"version": "2.0.0", "status": "draft"}),
        }
        initial = copy.deepcopy(self.remote.meta)
        for action in ("upload", "submit", "publish"):
            for field, change in changes.items():
                with self.subTest(action=action, field=field):
                    self.remote.meta = copy.deepcopy(initial)
                    plan = self.upload_plan() if action == "upload" else self.lifecycle_plan(action)
                    change(self.remote.meta)
                    self.assert_conflict(plan)


if __name__ == "__main__":
    unittest.main()
