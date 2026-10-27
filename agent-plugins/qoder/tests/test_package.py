# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Packaging contracts use a tiny adapter fixture, never unfinished Qoder/core tests."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location("qoder_package_" + name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load_script("build")
check = load_script("check_package")
VERSION = "0.1.0-dev.1"
# This fixture checks archive/build/protocol wiring, not the real registry implementation.
FIXTURE_MAIN = '''import argparse
import json
import sys
import yaml
from nacos_registry import __version__ as core_version
from nacos_registry.service import status
from . import __version__

assert core_version == __version__


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--state-dir")
    parser.add_argument("action")
    args = parser.parse_args()
    assert args.state_dir
    if args.action == "status":
        print(json.dumps(status()))
        return
    for line in sys.stdin:
        call = json.loads(line)
        if "id" not in call:
            continue
        if call["method"] == "initialize":
            result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}},
                      "serverInfo": {"name": "nacos-ai-registry", "version": __version__}}
        elif call["method"] == "tools/list":
            result = {"tools": [{"name": "nacos_" + name} for name in ("status", "scan", "search")]}
        else:
            result = {"content": [{"type": "text", "text": json.dumps(status())}]}
        print(json.dumps({"jsonrpc": "2.0", "id": call["id"], "result": result}))
'''


class ArchiveTests(unittest.TestCase):
    def test_sorted_fixed_metadata_and_reproducible_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            a, b = Path(temporary) / "a.zip", Path(temporary) / "b.zip"
            entries = {"z.py": b"last", ".qoder-plugin/plugin.json": b"{}", "a.py": b"first"}
            build.write_zip(a, entries)
            build.write_zip(b, dict(reversed(list(entries.items()))))
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(check.read_archive(a, checksum=False), entries)
            with zipfile.ZipFile(a) as archive:
                self.assertEqual(archive.namelist(), sorted(entries))
                for member in archive.infolist():
                    self.assertEqual(member.date_time, build.TIMESTAMP)
                    self.assertEqual(member.external_attr >> 16, 0o100644)
                    self.assertEqual(member.create_system, 3)
                    self.assertEqual(member.compress_type, zipfile.ZIP_STORED)

    def test_reject_unsafe_archive_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            for name in ("../secret", "/secret", "./file", "a\\b", "a/../secret"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    build.write_zip(Path(temporary) / "bad.zip", {name: b"no"})

    def test_hash_covers_dotfiles_names_and_content(self):
        original = {"qoder/.mcp.json": b"{}", "qoder/src/nacos_registry/service.py": b"x"}
        self.assertEqual(build.tree_sha256(original), build.tree_sha256(dict(reversed(list(original.items())))))
        self.assertNotEqual(build.tree_sha256(original), build.tree_sha256({**original, "qoder/.gitignore": b"dist/"}))
        self.assertNotEqual(build.tree_sha256(original),
                            build.tree_sha256({**original, "qoder/src/nacos_registry/service.py": b"y"}))

    def test_source_and_runtime_entries_ignore_other_plugins(self):
        entries = {"LICENSE": b"license", "qoder/src/nacos_registry/service.py": b"local",
                   "qoder/vendor/pyyaml/yaml/__init__.py": b"yaml", "codex/src/foreign.py": b"foreign"}
        self.assertNotIn("codex/src/foreign.py", check.source_entries(entries))
        runtime = build.runtime_entries(entries)
        self.assertEqual(runtime["nacos_registry/service.py"], b"local")
        self.assertEqual(runtime["yaml/__init__.py"], b"yaml")
        self.assertNotIn("foreign.py", runtime)

    def test_filter_private_state_without_dropping_legitimate_dotfiles(self):
        for name in ("src/__pycache__/x.pyc", "skills/.env", "skills/.env.local", "tests/credentials.json",
                     "tests/state.json", "tests/config.toml", "src/module.so", "skills/private.pem",
                     "src/.credential-key", "tests/.credential-key-temporary"):
            self.assertTrue(build.excluded(Path(name)), name)
        for name in (".qoder-plugin/plugin.json", ".mcp.json", ".gitignore", "skills/.metadata.json",
                     "src/nacos_registry/credentials.py"):
            self.assertFalse(build.excluded(Path(name)), name)

    def test_version_is_read_without_importing_adapter(self):
        self.assertEqual(build.literal_version(b'raise RuntimeError("not imported")\n__version__ = "0.1.0-dev.1"\n'), VERSION)
        with self.assertRaises(ValueError):
            build.literal_version(b'__version__ = str("0.1.0")')

    def test_checker_rejects_duplicate_and_other_host_manifests(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.zip"
            build.write_zip(path, {".codex-plugin/plugin.json": b"{}"})
            with self.assertRaisesRegex(ValueError, "Other host manifest"):
                check.read_archive(path, checksum=False)
            build.write_zip(path, {"plugin.json": b"{}"})
            with warnings.catch_warnings(), zipfile.ZipFile(path, "a") as archive:
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr("plugin.json", b"different")
            with self.assertRaisesRegex(ValueError, "sorted and unique"):
                check.read_archive(path, checksum=False)
            build.write_zip(path, {"plugin.json": b"{}"})
            with zipfile.ZipFile(path, "a") as archive:
                archive.writestr("extra", b"x")  # Non-fixed metadata must be rejected.
            with self.assertRaises(ValueError):
                check.read_archive(path, checksum=False)

    def test_environment_does_not_inherit_credentials(self):
        with patch.dict(os.environ, {"NACOS_PLUGIN_HOME": "/private/user-state", "TOKEN": "secret",
                                     "QODER_HOME": "/private/qoder", "PYTHONPATH": "/private/packages"}):
            env = check.isolated_env(Path("/isolated/home"))
        self.assertEqual(env["HOME"], "/isolated/home")
        self.assertFalse({"TOKEN", "NACOS_PLUGIN_HOME", "QODER_HOME", "PYTHONPATH"} & env.keys())


class BuildContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="qoder-package-test-")
        self.addCleanup(self.temporary.cleanup)
        self.parent = Path(self.temporary.name).resolve()
        self.root = self.parent / "qoder"
        self.root.mkdir()
        manifest = {"name": "nacos-ai-registry", "displayName": "Nacos AI Registry", "version": VERSION,
                    "description": "Fixture description", "descriptionZh": "夹具描述",
                    "homepage": "https://nacos.io/", "repository": "https://example.org/fixture",
                    "category": "developer-tools", "keywords": ["nacos"], "tags": ["skill"],
                    "logo": "./assets/nacos-icon.png",
                    "skills": "./skills/", "mcpServers": "./.mcp.json"}
        mcp = {"mcpServers": {"nacos-ai-registry": {"command": "python3",
               "args": ["${QODER_PLUGIN_ROOT}/server/nacos-qoder.pyz", "serve"]}}}
        fixture = {".qoder-plugin/plugin.json": json.dumps(manifest), ".mcp.json": json.dumps(mcp),
                   ".gitignore": "dist/\n", "requirements-build.txt": "PyYAML==6.0.3\n",
                   "README.md": "# Fixture adapter README\n",
                   "specs/compatibility.json": "{}", "src/nacos_qoder/__init__.py": '__version__ = "' + VERSION + '"\n',
                   "src/nacos_qoder/__main__.py": FIXTURE_MAIN,
                   "src/nacos_qoder/server.py": "# fixture\n", "src/nacos_qoder/service.py": "# fixture\n",
                   "src/nacos_qoder/host.py": "# fixture\n", "tests/test_package.py": "# fixture\n",
                   "skills/nacos-setup/SKILL.md": "---\nname: nacos-setup\n---\nSetup fixture\n",
                   "skills/nacos-registry/SKILL.md": "---\nname: nacos-registry\n---\nRegistry fixture\n",
                   "skills/nacos-find-capabilities/SKILL.md":
                       "---\nname: nacos-find-capabilities\n---\nDiscovery fixture\n",
                   "skills/nacos-find-capabilities/references/task-completion.md": "Reuse fixture\n",
                   "skills/.metadata.json": "{}",
                   # The stub exercises dependency export; no installed dependency is needed by these tests.
                   "vendor/pyyaml/yaml/__init__.py": '__version__ = "6.0.3"\n',
                   "vendor/pyyaml/LICENSE": "MIT test fixture license\n",
                   "LICENSE": "Apache-2.0 test fixture license\n"}
        fixture.update({"src/nacos_registry/" + name + ".py": "# local core fixture\n"
                        for name in build.CORE_MODULES})
        fixture.update({"src/nacos_registry/__init__.py": '__version__ = "' + VERSION + '"\n',
                        "src/nacos_registry/schema.py": "def validate(value):\n    return value\n",
                        "src/nacos_registry/service.py": "from .schema import validate\n\n"
                                                           "def status():\n    return validate({'profile': None})\n"})
        for name, data in fixture.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(data, encoding="utf-8")
        icon = self.root / "assets/nacos-icon.png"
        icon.parent.mkdir(exist_ok=True)
        icon.write_bytes(b"\x89PNG\r\n\x1a\n" + b"fixture icon")
        for name in ("build.py", "check_package.py"):
            target = self.root / "scripts" / name
            target.parent.mkdir(exist_ok=True)
            target.write_bytes((ROOT / "scripts" / name).read_bytes())
        self.core = self.root / "src/nacos_registry"

    def build_fixture(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return build.build(self.root)

    def test_complete_source_offline_rebuild_and_isolated_protocol(self):
        installer, source_path = self.build_fixture()
        with contextlib.redirect_stdout(io.StringIO()):
            check.check_packages(installer, source_path)
        source = check.read_archive(source_path)
        installer_files = check.read_archive(installer)
        self.assertEqual(check.source_entries(installer_files), check.source_entries(source))
        self.assertIn("qoder/.qoder-plugin/plugin.json", source)
        self.assertIn("qoder/.mcp.json", source)
        self.assertIn("qoder/.gitignore", source)
        self.assertIn("qoder/README.md", source)
        self.assertIn("qoder/skills/.metadata.json", source)
        self.assertEqual(source["qoder/src/nacos_registry/__init__.py"],
                         ('__version__ = "' + VERSION + '"\n').encode())
        self.assertTrue(all(name.startswith("qoder/") or name in {"LICENSE", "build-info.json"}
                            for name in source))
        self.assertFalse(any(name.startswith("codex/") for name in installer_files))
        with zipfile.ZipFile(io.BytesIO(installer_files["server/nacos-qoder.pyz"])) as runtime:
            self.assertEqual(runtime.read("__main__.py"), build.ENTRYPOINT)
            self.assertIn("yaml/LICENSE", runtime.namelist())
            self.assertIn("nacos_registry/schema.py", runtime.namelist())
            self.assertIn("nacos_registry/service.py", runtime.namelist())

    def test_standalone_without_codex_or_git_rebuilds_and_runs_cli_mcp(self):
        renamed = self.parent / "standalone-plugin"
        self.root.rename(renamed)
        self.root = renamed
        self.assertEqual(list(self.parent.iterdir()), [self.root])
        self.assertFalse((self.parent / "codex").exists())
        self.assertFalse((self.parent / ".git").exists())
        home = self.parent / "empty-home"
        home.mkdir()
        env = check.isolated_env(home)
        # Initial build, not just the export rebuild, must work with no site packages.
        check.run([sys.executable, "-I", "-S", "-B", str(self.root / "scripts/build.py")], self.root, env)
        installer = self.root / "dist" / f"nacos-ai-registry-qoder-{VERSION}.zip"
        source_path = installer.with_name(installer.stem + "-source.zip")
        info = json.loads(check.read_archive(source_path)["build-info.json"])
        self.assertIsNone(info["gitBase"])
        self.assertTrue(info["dirty"])
        self.assertEqual(info["localCore"]["version"], VERSION)
        # Includes offline source/install rebuilds and isolated CLI + MCP handshake/status.
        with contextlib.redirect_stdout(io.StringIO()):
            check.check_packages(installer, source_path)
        self.assertFalse((self.parent / "codex").exists())

    def test_build_does_not_delete_unrelated_dist_or_sources(self):
        dist = self.root / "dist"
        dist.mkdir()
        sentinel = dist / "user-file.txt"
        sentinel.write_text("keep", encoding="utf-8")
        inputs, _ = build.source_inputs(self.root)
        installer, source = self.build_fixture()
        before = installer.read_bytes(), source.read_bytes()
        self.build_fixture()
        self.assertEqual(before, (installer.read_bytes(), source.read_bytes()))
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
        self.assertEqual(inputs, build.source_inputs(self.root)[0])
        self.assertFalse((dist / "marketplace").exists())

    def test_no_sibling_sources_private_files_or_bytecode(self):
        for name in ("src/__pycache__/ignored.pyc", "skills/.env.local", "tests/state.json", "tests/auth.json",
                     "vendor/pyyaml/yaml/_yaml.so"):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"private/cache")
        # An unavailable sibling must never be traversed or required by the build.
        (self.parent / "codex").symlink_to(self.parent / "unavailable-sibling", target_is_directory=True)
        installer, source_path = self.build_fixture()
        for archive in (installer, source_path):
            entries = check.read_archive(archive)
            self.assertFalse(any(build.excluded(Path(name)) for name in entries))
            self.assertFalse(any(name.startswith("codex/") for name in entries))
            self.assertIn("qoder/src/nacos_registry/__init__.py", entries)

    def test_missing_local_core_dependencies_fail(self):
        for name in build.CORE_MODULES:
            path = self.core / (name + ".py")
            data = path.read_bytes()
            with self.subTest(module=name):
                path.unlink()
                try:
                    with self.assertRaisesRegex(ValueError, "Incomplete Qoder source tree"):
                        self.build_fixture()
                finally:
                    path.write_bytes(data)

    def test_wrong_local_core_version_fails(self):
        (self.core / "__init__.py").write_text('__version__ = "0.1.0-dev.15"\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "local core/plugin version mismatch"):
            self.build_fixture()

    def test_checker_rejects_sibling_sources_and_local_core_provenance_tampering(self):
        installer_path, source_path = self.build_fixture()
        source = check.read_archive(source_path)
        install = check.read_archive(installer_path)
        info = json.loads(source["build-info.json"])
        foreign = {"codex/src/nacos_registry/__init__.py": b"foreign"}
        with self.assertRaisesRegex(ValueError, "only independent Qoder sources"):
            check.check_source({**source, **foreign}, info, VERSION)
        with patch.object(check, "read_archive", side_effect=[{**install, **foreign}, source]):
            with self.assertRaisesRegex(ValueError, "Unexpected installer member"):
                check.check_packages(installer_path, source_path)
        altered_info = {**info, "localCore": {**info["localCore"], "sourceTreeSha256": "0" * 64}}
        with self.assertRaisesRegex(ValueError, "local core provenance mismatch"):
            check.check_source(source, altered_info, VERSION)
        altered_core = {**source, "qoder/src/nacos_registry/__init__.py": b'__version__ = "0.1.0-dev.15"\n'}
        altered_info = {**info, "sourceTreeSha256": build.tree_sha256(check.source_entries(altered_core))}
        with self.assertRaisesRegex(ValueError, "local core/plugin version mismatch"):
            check.check_source(altered_core, altered_info, VERSION)

    def test_wrong_manifest_or_dependency_version_fails(self):
        manifest_path = self.root / ".qoder-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] = "0.1.0-dev.15"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "manifest name/version"):
            self.build_fixture()
        manifest["version"] = VERSION
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        (self.root / "vendor/pyyaml/yaml/__init__.py").write_text('__version__ = "6.0.2"\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PyYAML version mismatch"):
            self.build_fixture()

    def test_input_and_output_symlinks_are_rejected(self):
        link = self.root / "src/nacos_qoder/linked.py"
        link.symlink_to(self.core / "__init__.py")
        with self.assertRaisesRegex(ValueError, "Source symlink"):
            self.build_fixture()
        link.unlink()
        (self.root / "dist").symlink_to(self.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "dist must not be a symlink"):
            self.build_fixture()

    def test_checksum_and_manifest_placeholder_tampering(self):
        installer, source_path = self.build_fixture()
        checksum = installer.with_suffix(".zip.sha256")
        checksum.write_text("0" * 64 + "  " + installer.name + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Checksum/name mismatch"):
            check.read_archive(installer)
        entries = check.read_archive(source_path)
        mcp = json.loads(entries["qoder/.mcp.json"])
        mcp["mcpServers"]["nacos-ai-registry"]["args"][0] = "${CODEX_PLUGIN_ROOT}/server/nacos-qoder.pyz"
        entries["qoder/.mcp.json"] = json.dumps(mcp).encode()
        with self.assertRaisesRegex(ValueError, "Qoder placeholder"):
            check.check_manifest(entries, VERSION, "qoder/")


if __name__ == "__main__":
    unittest.main()
