# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Minimal owned TOML blocks. Preserve all unrelated bytes and user tool policies."""
import hashlib
import getpass
import json
import os
from pathlib import Path
import re
import socket
import tomllib
from urllib.parse import urlsplit
from ..errors import PluginError, require
from ..store import safe_path


def local_defaults(validate_root):
    """Suggest local defaults without scanning skills or writing configuration.

    The MCP process runs from the installed plugin, not the conversation's project.
    Never infer a project path from its cwd. Existing profiles are not migrated.
    """
    result = {"scanRoots": [], "installRoots": [], "codexConfig": "", "warnings": []}

    def label(read, fallback):
        try:
            value = "".join(c for c in read() if c.isprintable()).strip()[:200]
            if value: return value
        except (OSError, RuntimeError, KeyError, ImportError):
            pass
        if "defaultIdentityUnavailable" not in result["warnings"]:
            result["warnings"].append("defaultIdentityUnavailable")
        return fallback

    result.update(id=label(socket.gethostname, "primary"), identityId=label(getpass.getuser, "current-user"))

    def directory(path):
        path = validate_root(path)
        require(all(not part.exists() or part.is_dir() for part in [path, *path.parents]), "Expected a directory")
        return path

    try: home = Path.home()
    except (OSError, RuntimeError):
        result["warnings"].extend(["defaultSkillsUnavailable", "defaultConfigUnavailable"])
        return result
    try:
        personal = directory(home / ".agents/skills")
        result["installRoots"] = [str(personal)]
        if personal.is_dir(): result["scanRoots"].append(str(personal))
    except (PluginError, OSError, ValueError, RuntimeError):
        result["warnings"].append("defaultSkillsUnavailable")
    codex_home = None
    try:
        candidate = Path(os.environ.get("CODEX_HOME") or home / ".codex").expanduser()
        require(candidate.is_absolute(), "CODEX_HOME must be absolute")
        codex_home = safe_path(candidate)
        require(all(not part.exists() or part.is_dir() for part in [codex_home, *codex_home.parents]), "Expected a directory")
        config = safe_path(codex_home / "config.toml")
        require(not config.exists() or config.is_file(), "Expected a configuration file")
        result["codexConfig"] = str(config)
    except (PluginError, OSError, ValueError, RuntimeError):
        result["warnings"].append("defaultConfigUnavailable")
    if codex_home:
        try:
            legacy = directory(codex_home / "skills")
            if legacy.is_dir() and str(legacy) not in result["scanRoots"]:
                result["scanRoots"].append(str(legacy))
        except (PluginError, OSError, ValueError, RuntimeError):
            result["warnings"].append("defaultScanUnavailable")
    return result


def read_config(path):
    p = safe_path(path)
    data = p.read_bytes() if p.exists() else b""
    tomllib.loads(data.decode())
    return data


def trial_tool_allowed(config_path, url, tool=None):
    """A trial route must not bypass an existing native server/tool restriction."""
    if not config_path:
        return True
    def identity(value):
        parsed = urlsplit(value)
        return (parsed.scheme.lower(), (parsed.hostname or "").lower(),
                parsed.port or (443 if parsed.scheme == "https" else 80), parsed.path.rstrip("/"), parsed.query)
    for entry in tomllib.loads(read_config(config_path).decode()).get("mcp_servers", {}).values():
        if not entry.get("url") or identity(entry["url"]) != identity(url):
            continue
        if entry.get("enabled") is False:
            return False
        if tool is not None and (tool in entry.get("disabled_tools", [])
                                 or ("enabled_tools" in entry and tool not in entry["enabled_tools"])):
            return False
    return True


def fingerprint(data):
    return hashlib.sha256(data).hexdigest()


def connection_key(name, connection_id):
    """Readable, bounded native name; the digest keeps resource scopes distinct."""
    require(isinstance(name, str) and isinstance(connection_id, str)
            and re.fullmatch(r"[a-f0-9]{64}", connection_id), "Invalid MCP identity")
    slug = re.sub(r"[^a-z0-9_-]+", "-", name.lower()).strip("-_")[:32].rstrip("-_") or "mcp"
    return f"nacos_{slug}_{connection_id[:12]}"


def connection_block(key, url, auth):
    # Existing hash-only keys remain valid for recovery and old connection plans.
    require(re.fullmatch(r"nacos_(?:[a-f0-9]{20}|[a-z0-9][a-z0-9_-]{0,31}_[a-f0-9]{12})", key), "Invalid managed MCP key")
    lines = [f"# BEGIN NACOS {key}", f"[mcp_servers.{key}]", "url = " + json.dumps(url)]
    if auth["type"] == "bearer":
        lines.append("bearer_token_env_var = " + json.dumps(auth["tokenEnv"]))
    lines.append(f"# END NACOS {key}")
    return "\n".join(lines) + "\n"


def replace_connection(data, key, block, previous=None):
    """Prepare an atomic rename only when the previous owned block is intact."""
    if previous and previous["configKey"] != key:
        data = replace_block(data, previous["configKey"], "", previous["configBlock"])
        return replace_block(data, key, block)
    return replace_block(data, key, block, previous.get("configBlock") if previous else None)


def replace_block(data, key, block, previous=None):
    text = data.decode()
    pattern = re.compile(r"(?m)^# BEGIN NACOS " + re.escape(key) + r"\n.*?^# END NACOS " + re.escape(key) + r"\n?", re.S)
    matches = list(pattern.finditer(text))
    require(len(matches) <= 1, "Duplicate managed configuration block", "conflict")
    if matches:
        require(previous and matches[0].group() == previous, "Managed configuration was edited; preserve changes", "conflict")
        text = text[:matches[0].start()] + block + text[matches[0].end():]
    else:
        require(previous is None, "Managed configuration block was removed", "conflict")
        parsed = tomllib.loads(text)
        require(key not in parsed.get("mcp_servers", {}), "MCP key already owned by another configuration", "conflict")
        text += ("\n" if text and not text.endswith("\n") else "") + block
    tomllib.loads(text)
    return text.encode()
