# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
import getpass
from pathlib import Path
import socket

from nacos_registry.errors import PluginError, require


def local_defaults(validate_root):
    result = {"scanRoots": [], "installRoots": [], "warnings": []}
    for field, read, fallback in (("id", socket.gethostname, "primary"),
                                  ("identityId", getpass.getuser, "current-user")):
        try:
            value = "".join(c for c in read() if c.isprintable()).strip()[:200]
            require(bool(value), "Default identity unavailable")
            result[field] = value
        except (PluginError, OSError, RuntimeError, KeyError):
            result[field] = fallback
            result["warnings"].append("defaultIdentityUnavailable")
    try:
        root = validate_root(Path.home() / ".qoder/skills")
        require(all(not part.exists() or part.is_dir() for part in [root, *root.parents]), "Expected a Skill directory")
        result["installRoots"] = [str(root)]
        if root.is_dir():
            result["scanRoots"] = [str(root)]
    except (PluginError, OSError, RuntimeError, ValueError):
        result["warnings"].append("defaultSkillsUnavailable")
    return result
