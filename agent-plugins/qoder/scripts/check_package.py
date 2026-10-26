#!/usr/bin/env python3
# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Validate final Qoder archives, isolated stdio/CLI and dependency-free source rebuilds."""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("qoder_build", Path(__file__).with_name("build.py"))
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)
require = builder.require


def read_archive(path, checksum=True):
    if checksum:
        expected = hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.name + "\n"
        require(path.with_suffix(".zip.sha256").read_text(encoding="utf-8") == expected,
                f"Checksum/name mismatch: {path}")
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        names = [member.filename for member in members]
        require(names == sorted(set(names)), "ZIP members must be sorted and unique")
        require(sum(member.file_size for member in members) <= 100 * 1024 * 1024,
                "Unexpectedly large archive")
        for member in members:
            name = member.filename
            relative = PurePosixPath(name)
            require(name and not relative.is_absolute() and ".." not in relative.parts
                    and str(relative) == name and "\\" not in name and "\0" not in name,
                    f"Unsafe ZIP path: {name}")
            require(not member.is_dir() and member.create_system == 3
                    and member.date_time == builder.TIMESTAMP
                    and member.external_attr >> 16 == builder.FILE_MODE
                    and member.compress_type == zipfile.ZIP_STORED
                    and not member.extra and not member.comment, f"Unfixed ZIP metadata: {name}")
            require(not builder.excluded(relative), f"Private configuration/cache/binary included: {name}")
            require(not any(part.endswith("-plugin") and part != ".qoder-plugin"
                            for part in relative.parts if part.startswith(".")),
                    f"Other host manifest: {name}")
            require("marketplace" not in relative.parts and relative.name != "marketplace.json",
                    "Marketplace must not be generated")
        require(not archive.comment, "Archive comment must be empty")
        return {name: archive.read(name) for name in names}


def extract(entries, root):
    for name, data in entries.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def source_entries(entries):
    return {name: data for name, data in entries.items()
            if name.startswith("qoder/") or name == "LICENSE"}


def check_source(entries, info, version):
    require(all(name.startswith("qoder/") or name in {"LICENSE", "build-info.json"} for name in entries),
            "Source ZIP must contain only independent Qoder sources, license and provenance")
    sources = source_entries(entries)
    require(builder.tree_sha256(sources) == info["sourceTreeSha256"], "Source tree hash mismatch")
    needed = set(builder.REQUIRED) | {"LICENSE", "qoder/.qoder-plugin/plugin.json",
                                     "qoder/vendor/pyyaml/LICENSE", "qoder/vendor/pyyaml/yaml/__init__.py"}
    needed.update("qoder/" + name for name in builder.SOURCE_FILES)
    require(needed <= sources.keys(), f"Missing rebuild source: {sorted(needed - sources.keys())}")
    allowed_qoder = tuple("qoder/" + directory + "/" for directory in builder.SOURCE_DIRS) + ("qoder/vendor/pyyaml/",)
    require(all(not name.startswith("qoder/") or name.startswith(allowed_qoder)
                or name in {"qoder/" + file for file in builder.SOURCE_FILES} for name in sources),
            "Unexpected/private Qoder source layout")
    require(builder.literal_version(sources["qoder/src/nacos_qoder/__init__.py"]) == version,
            "Qoder source version mismatch")
    require(builder.literal_version(sources["qoder/src/nacos_registry/__init__.py"]) == version,
            "Qoder local core/plugin version mismatch")
    local_core = {name: data for name, data in sources.items() if name.startswith("qoder/src/nacos_registry/")}
    require(info["localCore"] == {"package": "nacos_registry", "version": version,
                                  "sourceTreeSha256": builder.tree_sha256(local_core)},
            "Qoder local core provenance mismatch")
    require(builder.literal_version(sources["qoder/vendor/pyyaml/yaml/__init__.py"]) == "6.0.3",
            "PyYAML source version mismatch")
    dependency = info["dependencies"]["PyYAML"]
    vendor = {name: data for name, data in sources.items() if name.startswith("qoder/vendor/pyyaml/")}
    require(dependency["version"] == "6.0.3" and dependency["implementation"] == "pure-python"
            and dependency["source"] == "https://pypi.org/project/PyYAML/6.0.3/"
            and dependency["sourceTreeSha256"] == builder.tree_sha256(vendor)
            and dependency["licenseSha256"] == hashlib.sha256(sources["qoder/vendor/pyyaml/LICENSE"]).hexdigest(),
            "Dependency provenance mismatch")
    require(set(info["dependencies"]) == {"PyYAML"}, "Unexpected vendored dependency")
    require(info["version"] == version and type(info["dirty"]) is bool
            and (info["gitBase"] is None or re.fullmatch(r"[0-9a-f]{40,64}", info["gitBase"]))
            and info["entrypoint"] == "nacos_qoder.__main__.main" and info["pythonRequires"] == ">=3.11",
            "Build provenance/version mismatch")
    return sources


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def check_manifest(entries, version, prefix=""):
    manifest = json.loads(entries[prefix + ".qoder-plugin/plugin.json"])
    require(manifest.get("name") == "nacos-ai-registry" and manifest.get("version") == version,
            "Qoder manifest name/version mismatch")
    require(manifest.get("skills") == "./skills/" and manifest.get("mcpServers") == "./.mcp.json",
            "Manifest skills/MCP references are not portable")
    for text in strings(manifest):
        require("${" not in text and "{{" not in text and not text.startswith(("/", "~", "file:")),
                "Manifest contains an unresolved placeholder/absolute local path")
        if text.startswith("./"):
            relative = PurePosixPath(text[2:])
            require(".." not in relative.parts and "\\" not in text, "Manifest reference escapes package")
            target = prefix + relative.as_posix()
            require(target in entries or any(name.startswith(target.rstrip("/") + "/") for name in entries),
                    f"Missing manifest reference: {text}")
    config = json.loads(entries[prefix + ".mcp.json"])
    require(set(config) == {"mcpServers"} and set(config["mcpServers"]) == {"nacos-ai-registry"},
            "Unexpected/user MCP configuration included")
    server = config["mcpServers"]["nacos-ai-registry"]
    require(server.get("command") == "python3"
            and server.get("args") == ["${QODER_PLUGIN_ROOT}/server/nacos-qoder.pyz", "serve"],
            "MCP launch command must use the Qoder placeholder and independent zipapp")
    require(set(server) <= {"command", "args", "timeout"}, "MCP configuration contains private env/cwd/credentials")
    require([text for text in strings(config) if "${" in text or "{{" in text]
            == ["${QODER_PLUGIN_ROOT}/server/nacos-qoder.pyz"], "Unexpected MCP placeholder")


def isolated_env(home):
    """No inherited Nacos/MCP/auth/Python settings, and no access to a real user home."""
    return {"PATH": os.defpath, "HOME": str(home), "USERPROFILE": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"), "XDG_STATE_HOME": str(home / ".state"),
            "XDG_CACHE_HOME": str(home / ".cache"), "APPDATA": str(home / ".config"),
            "LOCALAPPDATA": str(home / ".local"), "LANG": "C.UTF-8",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0"}


def run(command, cwd, env, input=None):
    result = subprocess.run(command, cwd=cwd, env=env, input=input, capture_output=True,
                            text=True, timeout=60)
    require(result.returncode == 0, f"Isolated command failed: {command}\n{result.stderr}")
    require(not result.stderr.strip(), f"Unexpected stderr: {result.stderr}")
    return result.stdout


def check_runtime(runtime_path, root, version, env):
    base = [sys.executable, "-I", "-S", "-B", str(runtime_path)]
    require(run(base + ["--version"], root, env).strip() == version, "Isolated zipapp version mismatch")
    state = root / "private-state"
    status = json.loads(run(base + ["--state-dir", str(state), "status"], root, env))
    require(status.get("profile", "missing") is None, "Status used an existing profile/credentials")
    calls = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "qoder-package-check", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "nacos_status", "arguments": {}}},
    ]
    output = run(base + ["--state-dir", str(state), "serve"], root, env,
                 "\n".join(json.dumps(call) for call in calls) + "\n")
    replies = [json.loads(line) for line in output.splitlines()]
    require(len(replies) == 3 and [reply.get("id") for reply in replies] == [1, 2, 3]
            and all(reply.get("jsonrpc") == "2.0" and "error" not in reply for reply in replies),
            "Invalid stdio initialize/tools/list/status handshake")
    initialized = replies[0]["result"]
    require(initialized["serverInfo"].get("name") in {"nacos-ai-registry", "nacos-ai-registry-qoder"}
            and initialized["serverInfo"].get("version") == version
            and initialized["protocolVersion"] == "2025-03-26"
            and "tools" in initialized["capabilities"], "MCP identity/version/capabilities mismatch")
    tools = replies[1]["result"]["tools"]
    names = [tool["name"] for tool in tools]
    require(len(names) == len(set(names)) and {"nacos_status", "nacos_scan", "nacos_search"} <= set(names),
            "Missing/duplicate registry MCP tools")
    result = replies[2]["result"]
    require(not result.get("isError"), "MCP status failed")
    value = result.get("structuredContent")
    if value is None:
        content = [item["text"] for item in result["content"] if item.get("type") == "text"]
        require(len(content) == 1, "MCP status needs one JSON text result")
        value = json.loads(content[0])
    require(value.get("profile", "missing") is None, "MCP status read user state/credentials")


def check_packages(archive_path, source_path):
    require(sys.version_info >= (3, 11), "Python 3.11+ required")
    install = read_archive(archive_path)
    source = read_archive(source_path)
    info = json.loads(install["build-info.json"])
    version = info["version"]
    require(re.fullmatch(builder.VERSION_PATTERN, version), "Invalid packaged version")
    expected_name = f"nacos-ai-registry-qoder-{version}"
    require(archive_path.name == expected_name + ".zip" and source_path.name == expected_name + "-source.zip",
            "Artifact filenames/version mismatch")
    require(source["build-info.json"] == install["build-info.json"], "Source/install provenance mismatch")
    sources = check_source(source, info, version)
    require(source_entries(install) == sources, "Installer does not contain the same complete source")
    check_manifest(install, version)
    check_manifest(source, version, "qoder/")
    for prefix in (".qoder-plugin/", "skills/"):
        copied = {name: data for name, data in install.items() if name.startswith(prefix)}
        originals = {name[len("qoder/"):]: data for name, data in sources.items()
                     if name.startswith("qoder/" + prefix)}
        require(copied == originals, f"Installation/source copy mismatch: {prefix}")
    require(install[".mcp.json"] == sources["qoder/.mcp.json"], "Installation/source MCP mismatch")
    extras = {"build-info.json", "server/nacos-qoder.pyz", ".mcp.json", "THIRD_PARTY_NOTICES.txt"}
    require(all(name in sources or name in extras or name.startswith((".qoder-plugin/", "skills/"))
                for name in install), "Unexpected installer member/host manifest")
    runtime = install["server/nacos-qoder.pyz"]
    runtime_files = read_archive(io.BytesIO(runtime), checksum=False)
    require(runtime_files == builder.runtime_entries(sources), "Runtime does not match complete source/vendor")
    require(runtime_files["__main__.py"] == builder.ENTRYPOINT, "Wrong zipapp entrypoint")
    require(sources["qoder/vendor/pyyaml/LICENSE"] in install["THIRD_PARTY_NOTICES.txt"],
            "PyYAML LICENSE not distributed")
    with tempfile.TemporaryDirectory(prefix="nacos-qoder-check-") as temporary:
        temporary = Path(temporary).resolve()
        home = temporary / "empty-home"
        home.mkdir()
        env = isolated_env(home)
        package = temporary / "install"
        package.mkdir()
        extract(install, package)
        check_runtime(package / "server/nacos-qoder.pyz", package, version, env)
        # -I -S excludes every site package, proving vendoring is enough for a fresh machine.
        for label, contents in (("source", source), ("installed-source", install)):
            folder = temporary / label
            folder.mkdir()
            extract(contents, folder)
            script = folder / "qoder/scripts/build.py"
            run([sys.executable, "-I", "-S", "-B", str(script)], folder, env)
            rebuilt = folder / "qoder/dist/nacos-ai-registry"
            require((rebuilt / "server/nacos-qoder.pyz").read_bytes() == runtime,
                    f"{label} rebuild changed runtime")
            require(json.loads((rebuilt / "build-info.json").read_text(encoding="utf-8")) == info,
                    f"{label} rebuild changed source hash/provenance")
            for original in (archive_path, source_path):
                generated = folder / "qoder/dist" / original.name
                require(generated.read_bytes() == original.read_bytes(), f"{label} rebuild changed {original.name}")
    print("PASS: checksums, fixed ZIP metadata, Qoder manifests/versions, complete licensed source, "
          "isolated CLI/stdio status and offline source/installed-source reproducibility")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Installation ZIP (defaults to current Qoder version)")
    parser.add_argument("--source", type=Path, help="Matching complete source ZIP")
    args = parser.parse_args()
    if args.archive:
        archive = args.archive.resolve()
    else:
        version = builder.literal_version((ROOT / "src/nacos_qoder/__init__.py").read_bytes())
        archive = ROOT / "dist" / f"nacos-ai-registry-qoder-{version}.zip"
    source = args.source.resolve() if args.source else archive.with_name(archive.stem + "-source.zip")
    try:
        check_packages(archive, source)
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"Package check failed: {exc}") from exc


if __name__ == "__main__":
    main()
