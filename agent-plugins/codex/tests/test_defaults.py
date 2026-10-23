# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Default suggestions must not scan resources, migrate identities or write files."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nacos_registry.hosts.codex import local_defaults
from nacos_registry.server import serve
from nacos_registry.service import Service
from nacos_registry.store import Store


class DefaultsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.home = self.root / "home"; self.home.mkdir()
        self.service = Service(Store(self.root / "state"))
        for mock in (patch("pathlib.Path.home", return_value=self.home),
                     patch.dict("os.environ", {"CODEX_HOME": ""}),
                     patch("socket.gethostname", return_value="sample-computer"),
                     patch("getpass.getuser", return_value="sample-user")):
            mock.start(); self.addCleanup(mock.stop)

    def defaults(self): return local_defaults(self.service.allowed_root)

    def test_missing_directories_are_suggested_without_creation_or_inventory(self):
        with patch.object(Path, "iterdir", side_effect=AssertionError("No inventory")), \
             patch.object(Path, "read_bytes", side_effect=AssertionError("No content read")):
            value = self.defaults()
        self.assertEqual(value["id"], "sample-computer")
        self.assertEqual(value["identityId"], "sample-user")
        self.assertEqual(value["installRoots"], [str(self.home / ".agents/skills")])
        self.assertEqual(value["scanRoots"], [])
        self.assertEqual(value["codexConfig"], str(self.home / ".codex/config.toml"))
        self.assertEqual(value["warnings"], [])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_existing_personal_and_legacy_roots_respect_custom_codex_home(self):
        personal = self.home / ".agents/skills"; personal.mkdir(parents=True)
        custom = self.root / "custom-codex"; (custom / "skills").mkdir(parents=True)
        (self.home / ".codex/skills").mkdir(parents=True)
        with patch.dict("os.environ", CODEX_HOME=str(custom)):
            value = self.defaults()
        self.assertEqual(value["scanRoots"], [str(personal), str(custom / "skills")])
        self.assertEqual(value["installRoots"], [str(personal)])
        self.assertEqual(value["codexConfig"], str(custom / "config.toml"))
        self.assertFalse((custom / "config.toml").exists())

    def test_invalid_config_home_does_not_fall_back_to_a_different_account(self):
        for configured in ("relative-home", str(self.root / "cache/codex")):
            with self.subTest(home=configured), patch.dict("os.environ", CODEX_HOME=configured):
                value = self.defaults()
                if configured == "relative-home":
                    self.assertEqual(value["codexConfig"], "")
                    self.assertIn("defaultConfigUnavailable", value["warnings"])
                else:
                    self.assertEqual(value["scanRoots"], [])
                    self.assertIn("defaultScanUnavailable", value["warnings"])

    def test_symlinks_and_non_directory_paths_are_not_suggested(self):
        target = self.root / "external"; target.mkdir()
        (self.home / ".agents").symlink_to(target, target_is_directory=True)
        (self.home / ".codex").write_text("not a directory")
        value = self.defaults()
        self.assertEqual(value["installRoots"], [])
        self.assertEqual(value["scanRoots"], [])
        self.assertEqual(value["codexConfig"], "")
        self.assertIn("defaultSkillsUnavailable", value["warnings"])
        self.assertIn("defaultConfigUnavailable", value["warnings"])
        self.assertEqual(list(target.iterdir()), [])

    def test_unknown_local_identity_and_home_remain_editable(self):
        with patch("socket.gethostname", side_effect=OSError), \
             patch("getpass.getuser", side_effect=KeyError), \
             patch("pathlib.Path.home", side_effect=RuntimeError):
            value = self.defaults()
        self.assertEqual(value["id"], "primary")
        self.assertEqual(value["identityId"], "current-user")
        self.assertEqual(value["installRoots"], [])
        self.assertIn("defaultIdentityUnavailable", value["warnings"])
        self.assertIn("defaultSkillsUnavailable", value["warnings"])

    def test_status_does_not_migrate_saved_ids_roots_or_context(self):
        profile = dict(id="stable-id", identityId="saved-user", namespaceId="public",
                       clientUrl="https://registry.example.org/nacos", adminUrl="https://registry.example.org/nacos",
                       allowedOperations=["read"], scanRoots=[], installRoots=[str(self.root / "custom-skills")])
        self.service.invoke("configure", {"profile": profile})
        before = self.service.store.file.read_bytes()
        status = self.service.invoke("status", {})
        with patch("socket.gethostname", return_value="new-computer"), patch("getpass.getuser", return_value="new-user"):
            changed = self.service.invoke("status", {})
        self.assertNotEqual(status["defaults"], changed["defaults"])
        self.assertEqual(status["profile"], changed["profile"])
        self.assertEqual(changed["profile"]["id"], "stable-id")
        self.assertEqual(changed["profile"]["scanRoots"], [])
        self.assertEqual(status["context"], changed["context"])
        self.assertEqual(self.service.store.file.read_bytes(), before)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_directory_prefill_is_only_a_draft_until_saved(self):
        draft = {key: value for key, value in self.defaults().items()
                 if key in ("scanRoots", "installRoots", "codexConfig")}
        requests = [{"id": 1, "method": "initialize", "params": {}},
                    {"id": 2, "method": "tools/call", "params": {"name": "nacos_open_center_panel",
                     "arguments": {"route": "settings", "draft": copy.deepcopy(draft)}}}]
        out = io.StringIO()
        serve(self.service, io.StringIO('\n'.join(json.dumps({"jsonrpc": "2.0", **r}) for r in requests)), out)
        result = json.loads(out.getvalue().splitlines()[1])["result"]["structuredContent"]
        self.assertEqual(result["draft"], draft)
        self.assertIsNone(self.service.invoke("status", {})["profile"])
        self.assertFalse(self.service.store.file.exists())
        self.assertEqual(list(self.home.iterdir()), [])
