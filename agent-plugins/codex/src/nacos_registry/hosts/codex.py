# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Minimal owned TOML blocks. Preserve all unrelated bytes and user tool policies."""
import hashlib
import json
import re
import tomllib
from ..errors import require
from ..store import safe_path


def read_config(path):
    p = safe_path(path)
    data = p.read_bytes() if p.exists() else b""
    tomllib.loads(data.decode())
    return data


def fingerprint(data):
    return hashlib.sha256(data).hexdigest()


def connection_block(key, url, auth):
    require(re.fullmatch(r"nacos_[a-f0-9]{20}", key), "Invalid managed MCP key")
    lines = [f"# BEGIN NACOS {key}", f"[mcp_servers.{key}]", "url = " + json.dumps(url)]
    if auth["type"] == "bearer":
        lines.append("bearer_token_env_var = " + json.dumps(auth["tokenEnv"]))
    lines.append(f"# END NACOS {key}")
    return "\n".join(lines) + "\n"


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
