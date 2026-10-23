#!/usr/bin/env python3
# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Build a self-contained source zipapp and one-plugin ZIP, without network access."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
from nacos_registry import __version__
from nacos_registry.package import metadata
import yaml


def build():
    if sys.version_info < (3, 11): raise SystemExit("Python 3.11+ required")
    if yaml.__version__ != "6.0.3": raise SystemExit("Install requirements-build.txt first")
    manifest = json.loads((ROOT / "plugin.json").read_text())
    assert manifest["version"] == __version__
    license_path = next(path for path in (ROOT / "LICENSE", AGENT_ROOT / "LICENSE", AGENT_ROOT.parent / "LICENSE") if path.is_file())
    # Export only this adapter and the shared specs, preserving their sibling layout.
    sources = sorted(p for directory in ("src", "skills", "assets", "tests", "scripts", "docs", "specs", "examples") for p in (ROOT / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    sources += [ROOT / name for name in ("README.md", "requirements-build.txt", ".gitignore", "plugin.json", "mcp.json", ".mcp.json")]
    sources += sorted((AGENT_ROOT / "specs").rglob("*.md"))
    sources += [AGENT_ROOT / "README.md"]
    inputs = [(source, source.relative_to(AGENT_ROOT).as_posix()) for source in sources]
    inputs.append((license_path, "LICENSE"))
    inputs.sort(key=lambda item: item[1])
    source_hash = hashlib.sha256()
    for source, name in inputs:
        source_hash.update(name.encode() + b"\0" + source.read_bytes() + b"\0")
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    package = destination / "nacos-ai-registry"
    with tempfile.TemporaryDirectory() as temporary:
        staging = Path(temporary)
        app = staging / "app"
        app.mkdir()
        shutil.copytree(ROOT / "src/nacos_registry", app / "nacos_registry", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(Path(yaml.__file__).parent, app / "yaml", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.so", "*.pyd"))
        (app / "__main__.py").write_text("from nacos_registry.__main__ import main\nmain()\n")
        dist = importlib.metadata.distribution("PyYAML")
        licenses = [x for x in dist.files if x.name == "LICENSE"]
        assert licenses, "PyYAML license missing"
        license_text = dist.locate_file(licenses[0]).read_text()
        bundle = staging / "plugin"
        bundle.mkdir()
        for source, name in inputs:
            target = bundle / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source, target)
        for name in ("plugin.json", "mcp.json", ".mcp.json"):
            shutil.copy(ROOT / name, bundle / name)
        shutil.copytree(ROOT / "skills", bundle / "skills")
        shutil.copytree(ROOT / "assets", bundle / "assets")
        (bundle / "server").mkdir()
        # Fixed metadata and sorted members yield repeatable archives across build times.
        with zipfile.ZipFile(bundle / "server/nacos-registry.pyz", "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(app.rglob("*")):
                if file.is_file():
                    info = zipfile.ZipInfo(file.relative_to(app).as_posix(), (2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, file.read_bytes())
        (bundle / "THIRD_PARTY_NOTICES.txt").write_text("PyYAML 6.0.3 (pure Python)\nhttps://pyyaml.org/\n\n" + license_text)
        for skill in bundle.glob("skills/*/SKILL.md"): metadata(skill.read_bytes())
        assert (bundle / manifest["extensions"]["com.openai"]["onboardingSkill"]).is_file()
        # Compatibility fallback for local clients that still require the legacy manifest.
        overlay = {"name": manifest["name"], "version": __version__, "description": manifest["description"],
                   "skills": "./skills/", "mcpServers": "./.mcp.json", **manifest["extensions"]["com.openai"]}
        overlay.pop("onboardingSkill", None)
        overlay["extensions"] = {"com.openai": {"onboardingSkill": "./skills/setup/SKILL.md"}}
        (bundle / ".codex-plugin").mkdir()
        (bundle / ".codex-plugin/plugin.json").write_text(json.dumps(overlay, indent=2) + "\n")
        if package.exists(): shutil.rmtree(package)
        shutil.copytree(bundle, package)
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        dirty = subprocess.run(["git", "status", "--porcelain", "--", ROOT.name, "specs", "README.md", str(license_path)], cwd=AGENT_ROOT, capture_output=True, text=True)
        build_info = {"version": __version__, "sourceTreeSha256": source_hash.hexdigest(), "gitBase": revision.stdout.strip() or None, "dirty": bool(dirty.stdout), "dependencies": {"PyYAML": "6.0.3"}}
        (bundle / "build-info.json").write_text(json.dumps(build_info, indent=2) + "\n")
        shutil.copy(bundle / "build-info.json", package / "build-info.json")
        output = destination / f"nacos-ai-registry-{__version__}.zip"
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(bundle.rglob("*")):
                if file.is_file():
                    info = zipfile.ZipInfo(file.relative_to(bundle).as_posix(), (2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, file.read_bytes())
        checksum = hashlib.sha256(output.read_bytes()).hexdigest()
        output.with_suffix(".zip.sha256").write_text(checksum + "  " + output.name + "\n")
        source_output = destination / f"nacos-ai-registry-{__version__}-source.zip"
        with zipfile.ZipFile(source_output, "w", zipfile.ZIP_DEFLATED) as archive:
            for source, name in inputs:
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, source.read_bytes())
        source_output.with_suffix(".zip.sha256").write_text(hashlib.sha256(source_output.read_bytes()).hexdigest() + "  " + source_output.name + "\n")
        market = destination / "marketplace"
        if market.exists(): shutil.rmtree(market)
        shutil.copytree(bundle, market / "plugins/nacos-ai-registry")
        (market / ".agents/plugins").mkdir(parents=True)
        (market / ".agents/plugins/marketplace.json").write_text(json.dumps({"name": "local-nacos-registry", "interface": {"displayName": "Local Nacos Registry"}, "plugins": [{"name": "nacos-ai-registry", "source": {"source": "local", "path": "./plugins/nacos-ai-registry"}, "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": manifest["extensions"]["com.openai"]["interface"]["category"]}]}, indent=2) + "\n")
        print(output)
        print(checksum)


if __name__ == "__main__": build()
