# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Bounded, non-executing Skill packages with path and reference validation."""
import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata
from urllib.parse import unquote, urlsplit
import zipfile

import yaml

from .errors import require, PluginError
from .store import safe_path

MAX_BYTES = 20 * 1024 * 1024
MAX_FILES = 2000
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class UniqueLoader(yaml.SafeLoader):
    pass


def mapping(loader, node, deep=False):
    result = {}
    for key, value in node.value:
        key = loader.construct_object(key, deep=deep)
        require(isinstance(key, str) and key not in result, "Duplicate or non-string YAML key")
        result[key] = loader.construct_object(value, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def metadata(data):
    require(len(data) <= 1024 * 1024, "SKILL.md exceeds 1 MiB")
    text = data.decode("utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    require(match is not None, "SKILL.md needs YAML frontmatter")
    # YAML aliases can amplify a tiny document; skill metadata needs neither aliases nor tags.
    try:
        depth = 0
        for count, token in enumerate(yaml.scan(match[1])):
            if isinstance(token, (yaml.tokens.BlockMappingStartToken, yaml.tokens.BlockSequenceStartToken, yaml.tokens.FlowMappingStartToken, yaml.tokens.FlowSequenceStartToken)):
                depth += 1
            elif isinstance(token, (yaml.tokens.BlockEndToken, yaml.tokens.FlowMappingEndToken, yaml.tokens.FlowSequenceEndToken)):
                depth -= 1
            require(count <= 10000 and depth <= 32, "YAML nesting/token limit exceeded")
            require(not isinstance(token, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken, yaml.tokens.TagToken)),
                    "YAML aliases, anchors and explicit tags are unsupported")
        value = yaml.load(match[1], Loader=UniqueLoader)
    except yaml.YAMLError:
        raise PluginError("validation", "Invalid YAML frontmatter") from None
    require(isinstance(value, dict), "Skill frontmatter must be a mapping")
    require(isinstance(value.get("name"), str) and len(value["name"]) <= 64 and NAME.fullmatch(value["name"]), "Invalid Skill name")
    require(isinstance(value.get("description"), str) and bool(value["description"].strip()), "Skill description is required")
    return value


def path_name(name):
    require(isinstance(name, str) and name and not any(ord(c) < 32 for c in name), "Invalid package path")
    require("\\" not in name and ":" not in name, "Nonportable package path")
    p = PurePosixPath(name)
    require(not p.is_absolute() and not any(x in ("", ".", "..") for x in name.split("/")), "Unsafe package path")
    return p.as_posix()


def validate(files):
    require(0 < len(files) <= MAX_FILES and sum(map(len, files.values())) <= MAX_BYTES, "Package limit exceeded")
    require("SKILL.md" in files, "Package must contain SKILL.md")
    folded = set()
    for name in files:
        path_name(name)
        key = unicodedata.normalize("NFC", name).casefold()
        require(key not in folded, "Duplicate/case-colliding package paths")
        folded.add(key)
        require(not any(PurePosixPath(name).as_posix().startswith(other + "/") for other in files if other != name), "File/directory path collision")
    meta = metadata(files["SKILL.md"])
    for name, content in files.items():
        if not name.lower().endswith(".md"):
            continue
        text = content.decode("utf-8")
        links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text)
        links += re.findall(r"^\s*\[[^\]]+\]:\s*(\S+)", text, re.M)
        for link in links:
            link = link.strip().split(' "', 1)[0].strip("<>")
            url = urlsplit(link)
            if url.scheme in ("https", "http", "mailto") or link.startswith("#"):
                continue
            require(not url.scheme and not url.netloc, "Unsupported reference URL")
            local = unquote(url.path)
            if not local:
                continue
            path_name(local)
            target = (PurePosixPath(name).parent / local).as_posix()
            require(target in files or any(x.startswith(target.rstrip("/") + "/") for x in files), "Missing package reference", "invalid_reference")
    return meta


def read_directory(root):
    root = safe_path(root)
    require(root.is_dir(), "Skill directory is missing")
    files, total = {}, 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            p = Path(directory)/name
            require(not p.is_symlink(), "Skill contains a symbolic link")
        for name in names:
            p = Path(directory)/name
            require(p.is_file(), "Skill contains a special file")
            require(p.stat().st_size <= MAX_BYTES - total, "Package exceeds size limit")
            data = p.read_bytes()
            total += len(data)
            require(total <= MAX_BYTES and len(files) < MAX_FILES, "Package limit exceeded")
            files[p.relative_to(root).as_posix()] = data
    validate(files)
    return files


def unpack(data):
    require(len(data) <= MAX_BYTES, "ZIP exceeds size limit")
    files, total = {}, 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            require(len(archive.infolist()) <= MAX_FILES, "ZIP has too many entries")
            for info in archive.infolist():
                name = path_name(info.filename.rstrip("/"))
                mode = info.external_attr >> 16
                kind = stat.S_IFMT(mode)
                require(kind in (0, stat.S_IFREG, stat.S_IFDIR), "ZIP contains a link or special file")
                require(not info.flag_bits & 1, "Encrypted ZIP is unsupported")
                if info.is_dir():
                    continue
                require(name not in files, "Duplicate ZIP entry")
                require(info.file_size <= MAX_BYTES - total, "Expanded ZIP exceeds limit")
                content = archive.read(info)
                total += len(content)
                require(total <= MAX_BYTES, "Expanded ZIP exceeds limit")
                files[name] = content
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError):
        raise PluginError("validation", "Unreadable ZIP") from None
    if "SKILL.md" not in files:
        roots = {x.split("/")[0] for x in files}
        require(len(roots) == 1, "ZIP must contain exactly one Skill")
        prefix = next(iter(roots)) + "/"
        require(prefix + "SKILL.md" in files, "ZIP must contain SKILL.md")
        files = {k[len(prefix):]: v for k, v in files.items()}
    validate(files)
    return files


def pack(files):
    validate(files)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return output.getvalue()


def hashes(files):
    return {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}


def disk_hashes(root):
    root = safe_path(root)
    if not root.exists():
        return None
    return hashes(read_directory(root))
