#!/usr/bin/env python3
# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Read-only checks for the combined Codex/Qoder GitHub Release attachments.

Run each adapter's check_package.py first. This script neither builds packages nor
accesses GitHub; --release-json accepts a saved GitHub REST release response.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_zip(path):
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        names = [item.filename for item in members]
        require(len(names) == len(set(names)), f"Duplicate ZIP entries: {path.name}")
        require(sum(item.file_size for item in members) <= 100 * 1024 * 1024,
                f"Unexpectedly large archive: {path.name}")
        for item in members:
            name = PurePosixPath(item.filename)
            require(not name.is_absolute() and ".." not in name.parts
                    and "\\" not in item.filename and not item.is_dir()
                    and not stat.S_ISLNK(item.external_attr >> 16),
                    f"Unsafe ZIP entry: {item.filename}")
        return {name: archive.read(name) for name in names}


def tree_hash(entries):
    digest = hashlib.sha256()
    for name, data in sorted(entries.items()):
        digest.update(name.encode() + b"\0" + data + b"\0")
    return digest.hexdigest()


def check(args):
    require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?", args.version),
            "Use a component version, such as 0.1.1 or 0.2.0-rc.1")
    require(re.fullmatch(r"[0-9a-f]{40}", args.commit), "Use the full release commit SHA")
    names = {}
    for host, prefix in (("codex", "nacos-ai-registry"), ("qoder", "nacos-ai-registry-qoder")):
        names[host] = (f"{prefix}-{args.version}.zip", f"{prefix}-{args.version}-source.zip")
    expected = {name + suffix for pair in names.values() for name in pair for suffix in ("", ".sha256")}
    actual = {path.name for path in args.artifacts_dir.iterdir()}
    require(actual == expected, f"Attachment set differs: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    digests = {}
    for name in sorted(expected):
        path = args.artifacts_dir / name
        require(path.is_file() and not path.is_symlink(), f"Not a regular attachment: {name}")
        digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    for host, (install_name, source_name) in names.items():
        for name in (install_name, source_name):
            checksum = (args.artifacts_dir / (name + ".sha256")).read_text()
            require(checksum == f"{digests[name]}  {name}\n", f"Checksum or filename mismatch: {name}")
        install = read_zip(args.artifacts_dir / install_name)
        source = read_zip(args.artifacts_dir / source_name)
        info = json.loads(install["build-info.json"])
        require(info["version"] == args.version and info["gitBase"] == args.commit
                and info["dirty"] is False, f"Wrong version, commit or dirty build: {host}")
        if "build-info.json" in source:
            require(json.loads(source["build-info.json"]) == info, f"Source provenance differs: {host}")
        inputs = {name: data for name, data in source.items() if name != "build-info.json"}
        require(tree_hash(inputs) == info["sourceTreeSha256"], f"Source tree hash differs: {host}")
        require(all(install.get(name) == data for name, data in inputs.items()),
                f"Source ZIP and bundled source differ: {host}")
        manifest = "plugin.json" if host == "codex" else ".qoder-plugin/plugin.json"
        require(json.loads(install[manifest])["version"] == args.version
                and json.loads(source[f"{host}/{manifest}"])["version"] == args.version,
                f"Manifest version differs: {host}")
        require("LICENSE" in source and f"{host}/scripts/check_package.py" in source,
                f"Missing license or package checker: {host}")
        print(f"PASS {host}: version, clean commit, source correspondence and SHA-256")

    if args.release_json:
        release = json.loads(args.release_json.read_text())
        notes = args.notes_file.read_text().replace("\r\n", "\n").strip()
        require(not re.search(r"\{\{[^}]+\}\}|<VERSION>|<FULL_MERGED_COMMIT_SHA>", notes),
                "Release notes still contain template placeholders")
        require(f"# Nacos AI Registry Agent Plugins {args.version}" in notes.splitlines(),
                "Release notes heading differs")
        require(release["tag_name"] == f"nacos-ai-registry-v{args.version}", "Wrong release tag")
        require(release["name"] == f"Nacos AI Registry Agent Plugins {args.version}", "Wrong release title")
        require(release["draft"] is (args.stage == "draft"), "Unexpected release stage")
        require(release["prerelease"] is ("-" in args.version), "Unexpected prerelease flag")
        if args.stage == "published":
            require(bool(release.get("published_at")), "Published release has no publication time")
        require(release["body"].replace("\r\n", "\n").strip() == notes, "Release notes differ")
        assets = release["assets"]
        require(len(assets) == len(expected) and {item["name"] for item in assets} == expected,
                "Remote attachment set differs")
        for item in assets:
            name = item["name"]
            require(item["state"] == "uploaded"
                    and item["size"] == (args.artifacts_dir / name).stat().st_size
                    and item.get("digest") == f"sha256:{digests[name]}",
                    f"Remote upload, size or SHA-256 differs: {name}")
        print(f"PASS GitHub {args.stage}: title, tag, flags, notes and all eight attachment digests")
    print("PASS: exactly eight release attachments; no files or remote state changed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--release-json", type=Path)
    parser.add_argument("--notes-file", type=Path)
    parser.add_argument("--stage", choices=("draft", "published"))
    args = parser.parse_args()
    if any((args.release_json, args.notes_file, args.stage)) and not all((args.release_json, args.notes_file, args.stage)):
        parser.error("--release-json, --notes-file and --stage must be supplied together")
    try:
        check(args)
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"FAIL: {exc}\n")


if __name__ == "__main__":
    main()
