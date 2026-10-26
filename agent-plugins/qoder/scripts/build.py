#!/usr/bin/env python3
# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Offline, reproducible Qoder installer and complete, independently buildable source."""
import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?"
PY_YAML_VERSION = "6.0.3"
TIMESTAMP = (2026, 1, 1, 0, 0, 0)
FILE_MODE = 0o100644
ENTRYPOINT = b"from nacos_qoder.__main__ import main\nmain()\n"
SOURCE_DIRS = ("src", "scripts", "tests", "skills", ".qoder-plugin", "specs")
SOURCE_FILES = (".mcp.json", "requirements-build.txt", ".gitignore")
CORE_MODULES = ("__init__", "schema", "service", "registry", "remote", "package", "store",
                "errors", "transport", "downstream", "credentials", "credential_service")
REQUIRED = tuple("qoder/src/nacos_qoder/" + name + ".py"
                 for name in ("__init__", "__main__", "server", "service", "host"))
REQUIRED += tuple("qoder/src/nacos_registry/" + name + ".py" for name in CORE_MODULES)
REQUIRED += ("qoder/specs/compatibility.json", "qoder/skills/nacos-setup/SKILL.md",
             "qoder/skills/nacos-registry/SKILL.md", "qoder/scripts/build.py",
             "qoder/scripts/check_package.py", "qoder/tests/test_package.py")
EXCLUDED_DIRS = {"__pycache__", ".git", ".venv", "venv", "dist", "node_modules",
                 ".pytest_cache", ".mypy_cache", ".ruff_cache", ".qoder", ".codex", ".idea"}
PRIVATE_FILES = {".DS_Store", "state.json", "state.lock", "credentials.json", "auth.json", ".credential-key",
                 "config.toml", ".netrc", ".npmrc", ".pypirc", "id_rsa", "id_ed25519"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def excluded(path):
    """Keep legitimate dotfiles, but never caches, local state or private configuration."""
    return (any(part in EXCLUDED_DIRS for part in path.parts)
            or path.name in PRIVATE_FILES or path.name == ".env" or path.name.startswith(".env.")
            or path.name.startswith(".credential-key-")
            or path.suffix.lower() in {".pyc", ".pyo", ".so", ".pyd", ".dylib", ".pem", ".key"})


def files_under(directory):
    require(directory.is_dir() and not directory.is_symlink(), f"Missing/source symlink: {directory}")
    for current, directories, filenames in os.walk(directory, followlinks=False):
        current = Path(current)
        directories[:] = sorted(name for name in directories if not excluded(Path(name)))
        for name in directories:
            require(not (current / name).is_symlink(), f"Source symlink: {current / name}")
        for name in sorted(filenames):
            relative = (current / name).relative_to(directory)
            if not excluded(relative):
                path = current / name
                require(path.is_file() and not path.is_symlink(), f"Source symlink/non-file: {path}")
                yield path


def literal_version(data):
    """Read a package version without importing its unfinished adapter or dependencies."""
    tree = ast.parse(data.decode("utf-8"))
    values = [ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)]
    require(len(values) == 1 and isinstance(values[0], str), "Missing literal __version__")
    return values[0]


def tree_sha256(entries):
    digest = hashlib.sha256()
    for name, data in sorted(entries.items()):
        digest.update(name.encode("utf-8") + b"\0" + data + b"\0")
    return digest.hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def write_zip(path, entries):
    """Stored members avoid zlib-version-dependent output; all metadata is fixed."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(entries.items()):
            parts = PurePosixPath(name)
            require(name and not parts.is_absolute() and ".." not in parts.parts
                    and "\\" not in name and "\0" not in name and str(parts) == name,
                    f"Unsafe archive member: {name}")
            info = zipfile.ZipInfo(name, TIMESTAMP)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = FILE_MODE << 16
            archive.writestr(info, data)


def dependency_sources(root):
    """Prefer exported vendoring; only the initial checkout needs installed PyYAML."""
    vendor = root / "vendor/pyyaml"
    if vendor.exists():
        package, license_path = vendor / "yaml", vendor / "LICENSE"
    else:
        try:
            distribution = importlib.metadata.distribution("PyYAML")
        except importlib.metadata.PackageNotFoundError as exc:
            raise ValueError("Install requirements-build.txt once; exported source rebuilds without pip") from exc
        require(distribution.version == PY_YAML_VERSION, "PyYAML must be exactly 6.0.3")
        package = Path(distribution.locate_file("yaml"))
        licenses = [file for file in distribution.files or () if file.name == "LICENSE"]
        require(len(licenses) == 1, "PyYAML LICENSE missing or ambiguous")
        license_path = Path(distribution.locate_file(licenses[0]))
    require(literal_version((package / "__init__.py").read_bytes()) == PY_YAML_VERSION,
            "Vendored PyYAML version mismatch")
    require(license_path.is_file() and not license_path.is_symlink(), "PyYAML LICENSE missing/linked")
    # Pure Python only, including loader/parser/emitter; never the optional _yaml extension.
    entries = {"qoder/vendor/pyyaml/yaml/" + file.relative_to(package).as_posix(): file.read_bytes()
               for file in files_under(package) if file.suffix == ".py"}
    require(entries, "PyYAML source missing")
    entries["qoder/vendor/pyyaml/LICENSE"] = license_path.read_bytes()
    return entries


def source_inputs(root):
    # The checkout directory may have any name; exported source always uses qoder/.
    entries = {}
    for name in SOURCE_DIRS:
        for file in files_under(root / name):
            entries["qoder/" + file.relative_to(root).as_posix()] = file.read_bytes()
    for name in SOURCE_FILES:
        file = root / name
        require(file.is_file() and not file.is_symlink(), f"Missing/linked source input: {file}")
        entries["qoder/" + name] = file.read_bytes()
    licenses = (root / "LICENSE", root.parent / "LICENSE", root.parent.parent / "LICENSE")
    license_path = next((file for file in licenses if file.is_file() and not file.is_symlink()), None)
    require(license_path is not None, "Project LICENSE missing")
    entries["LICENSE"] = license_path.read_bytes()
    entries.update(dependency_sources(root))
    return entries, license_path


def provenance(root, source_hash, license_path):
    # An exported tree has no .git. Carry forward provenance only for identical inputs.
    exported = root.parent / "build-info.json"
    if exported.is_file():
        value = json.loads(exported.read_text(encoding="utf-8"))
        if value.get("sourceTreeSha256") == source_hash:
            base, dirty = value.get("gitBase"), value.get("dirty")
            require(base is None or re.fullmatch(r"[0-9a-f]{40,64}", base), "Invalid exported gitBase")
            require(type(dirty) is bool, "Invalid exported dirty flag")
            return base, dirty
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root,
                             capture_output=True, text=True, timeout=10)
        if top.returncode or not root.is_relative_to(Path(top.stdout.strip()).resolve()):
            return None, True
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                                  capture_output=True, text=True, timeout=10)
        paths = [str(root / name) for name in (*SOURCE_DIRS, *SOURCE_FILES)]
        paths.append(str(license_path))
        if (root / "vendor").exists():
            paths.append(str(root / "vendor"))
        status = subprocess.run(["git", "status", "--porcelain", "--", *paths], cwd=root,
                                capture_output=True, text=True, timeout=10)
        return revision.stdout.strip() or None, bool(status.returncode or status.stdout)
    except (OSError, subprocess.TimeoutExpired):
        return None, True


def runtime_entries(sources):
    entries = {"__main__.py": ENTRYPOINT, "LICENSE": sources["LICENSE"]}
    for prefix in ("qoder/src/", "qoder/vendor/pyyaml/"):
        for name, data in sources.items():
            if name.startswith(prefix):
                runtime_name = name[len(prefix):]
                # The dependency license has a distinct location from the project license.
                if prefix == "qoder/vendor/pyyaml/" and runtime_name == "LICENSE":
                    runtime_name = "yaml/LICENSE"
                require(runtime_name not in entries, f"Runtime member collision: {runtime_name}")
                entries[runtime_name] = data
    return entries


def build(root=None):
    require(sys.version_info >= (3, 11), "Python 3.11+ required")
    root = (root or ROOT).resolve()
    sources, license_path = source_inputs(root)
    version = literal_version(sources["qoder/src/nacos_qoder/__init__.py"])
    require(re.fullmatch(VERSION_PATTERN, version), "Unsafe Qoder version")
    manifest = json.loads(sources["qoder/.qoder-plugin/plugin.json"])
    require(manifest.get("name") == "nacos-ai-registry" and manifest.get("version") == version,
            "Qoder manifest name/version mismatch")
    require(sources["qoder/requirements-build.txt"].decode().splitlines().count("PyYAML==6.0.3") == 1,
            "Build dependency must pin PyYAML==6.0.3")
    missing = set(REQUIRED) - sources.keys()
    require(not missing, f"Incomplete Qoder source tree: {sorted(missing)}")
    core_version = literal_version(sources["qoder/src/nacos_registry/__init__.py"])
    require(core_version == version, "Qoder local core/plugin version mismatch")
    local_core = {"package": "nacos_registry", "version": core_version,
                  "sourceTreeSha256": tree_sha256({name: data for name, data in sources.items()
                                                  if name.startswith("qoder/src/nacos_registry/")})}
    source_hash = tree_sha256(sources)
    base, dirty = provenance(root, source_hash, license_path)
    dependency = {"version": PY_YAML_VERSION, "implementation": "pure-python",
                  "source": "https://pypi.org/project/PyYAML/6.0.3/",
                  "sourceTreeSha256": tree_sha256({name: data for name, data in sources.items()
                                                  if name.startswith("qoder/vendor/pyyaml/")}),
                  "licenseSha256": hashlib.sha256(sources["qoder/vendor/pyyaml/LICENSE"]).hexdigest()}
    info = {"version": version, "sourceTreeSha256": source_hash, "gitBase": base, "dirty": dirty,
            "localCore": local_core, "dependencies": {"PyYAML": dependency}, "pythonRequires": ">=3.11",
            "entrypoint": "nacos_qoder.__main__.main"}
    exported = {**sources, "build-info.json": json_bytes(info)}
    bundle = dict(exported)  # Installation contains the *same* complete rebuildable source.
    for prefix in (".qoder-plugin/", "skills/"):
        for name, data in sources.items():
            if name.startswith("qoder/" + prefix):
                bundle[name[len("qoder/"):]] = data
    bundle[".mcp.json"] = sources["qoder/.mcp.json"]
    bundle["THIRD_PARTY_NOTICES.txt"] = (b"PyYAML 6.0.3 (pure Python)\n"
                                          b"https://pypi.org/project/PyYAML/6.0.3/\n\n"
                                          + sources["qoder/vendor/pyyaml/LICENSE"])
    destination = root / "dist"
    require(not destination.is_symlink(), "dist must not be a symlink")
    destination.mkdir(exist_ok=True)
    package = destination / "nacos-ai-registry"
    output = destination / f"nacos-ai-registry-qoder-{version}.zip"
    source_output = destination / f"nacos-ai-registry-qoder-{version}-source.zip"
    with tempfile.TemporaryDirectory(prefix="nacos-qoder-build-") as temporary:
        staging = Path(temporary)
        runtime = staging / "nacos-qoder.pyz"
        write_zip(runtime, runtime_entries(sources))
        bundle["server/nacos-qoder.pyz"] = runtime.read_bytes()
        staged_package = staging / "plugin"
        staged_package.mkdir()
        for name, data in sorted(bundle.items()):
            target = staged_package / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o644)
        for target, contents in ((output, bundle), (source_output, exported)):
            staged_zip = staging / target.name
            write_zip(staged_zip, contents)
            require(not target.is_symlink(), f"Output must not be a symlink: {target}")
            checksum_path = target.with_suffix(".zip.sha256")
            require(not checksum_path.is_symlink(), f"Checksum must not be a symlink: {checksum_path}")
            checksum = hashlib.sha256(staged_zip.read_bytes()).hexdigest()
            staged_sum = staging / checksum_path.name
            staged_sum.write_text(checksum + "  " + target.name + "\n", encoding="utf-8")
            os.replace(staged_zip, target)
            os.replace(staged_sum, checksum_path)
        # Delete only this builder's local install directory, never all dist or source.
        require(not package.is_symlink(), "Install output must not be a symlink")
        if package.exists():
            require(package.is_dir(), "Install output is not a directory")
            shutil.rmtree(package)
        shutil.copytree(staged_package, package)
    print(output)
    print(source_output)
    print(f"Local Qoder install directory: {package}")
    return output, source_output


def main():
    try:
        build()
    except (ValueError, OSError, KeyError, SyntaxError) as exc:
        raise SystemExit(f"Build failed: {exc}") from exc


if __name__ == "__main__":
    main()
