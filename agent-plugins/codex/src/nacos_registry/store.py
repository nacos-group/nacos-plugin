# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Versioned local facts and serialized operations. No remote transaction claims."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import uuid

from .errors import require


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def new_id():
    return uuid.uuid4().hex


def safe_path(path):
    path = Path(path).absolute()
    # macOS exposes its system temporary directories through fixed root aliases.
    # Canonicalize these OS aliases, while rejecting user/package-controlled links.
    for alias in (Path("/var"), Path("/tmp")):
        if alias.is_symlink() and alias.resolve() == Path("/private") / alias.name and (path == alias or alias in path.parents):
            path = alias.resolve() / path.relative_to(alias)
    for part in [path, *path.parents]:
        require(not part.is_symlink(), "Symbolic links are not supported in managed paths")
    return path.resolve()


def atomic_write(path, content):
    path = safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class Store:
    def __init__(self, root=None):
        self.root = safe_path(root or os.environ.get("NACOS_PLUGIN_HOME", Path.home()/".local/state/nacos-ai-registry"))
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        self.file = self.root / "state.json"
        self.data = None

    @contextlib.contextmanager
    def locked(self):
        lock = safe_path(self.root / "state.lock")
        with open(lock, "a+b") as stream:
            os.chmod(lock, 0o600)
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                if self.file.exists():
                    self.data = json.loads(safe_path(self.file).read_text())
                    require(self.data.get("schemaVersion") == 1, "Unknown state schema; original data retained", "state_schema")
                else:
                    self.data = {"schemaVersion": 1, "profile": None, "plans": {}, "installations": {},
                                 "bindings": {}, "scans": {}, "operations": {}, "connections": {}, "tasks": {},
                                 "onboarding": {"status": "not_started"}}
                yield self
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def save(self):
        atomic_write(self.file, json.dumps(self.data, ensure_ascii=False, indent=2).encode())

    def artifact(self, identifier, suffix=".zip"):
        require(len(identifier) == 32 and all(c in "0123456789abcdef" for c in identifier), "Invalid artifact ID")
        return safe_path(self.root / "artifacts" / (identifier + suffix))

    def operation(self, action, target):
        identifier = new_id()
        self.data["operations"][identifier] = {"id": identifier, "action": action, "target": target, "status": "running",
                                              "context": digest(self.data["profile"]), "createdAt": time.time()}
        self.save()
        return self.data["operations"][identifier]
