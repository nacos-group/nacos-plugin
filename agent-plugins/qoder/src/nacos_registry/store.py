# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Versioned local facts and serialized operations. No remote transaction claims."""
import contextlib
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
import tempfile
import time
import uuid

from .errors import PluginError, require


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
        self.root = safe_path(root or os.environ.get("NACOS_QODER_HOME") or Path.home()/".qoder/state/nacos-ai-registry")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        self.file = self.root / "state.json"
        self.data = None
        self._locked = False
        self.credential_reader = None

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
                self._locked = True
                yield self
            finally:
                self._locked = False
                fcntl.flock(stream, fcntl.LOCK_UN)

    def save(self):
        atomic_write(self.file, json.dumps(self.data, ensure_ascii=False, indent=2).encode())

    def _credential_key(self):
        require(self._locked, "Credential key access requires the state lock")
        root = safe_path(self.root)
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            metadata = os.fstat(directory)
            require(metadata.st_uid == os.getuid() and stat.S_IMODE(metadata.st_mode) == 0o700,
                    "Credential state directory must be private and owned by the current user")
            key_path = safe_path(root / ".credential-key")
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            try:
                descriptor = os.open(key_path.name, flags, dir_fd=directory)
            except FileNotFoundError:
                temporary = ".credential-key-" + new_id()
                descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                     0o600, dir_fd=directory)
                try:
                    with os.fdopen(descriptor, "wb") as stream:
                        os.fchmod(stream.fileno(), 0o600)
                        stream.write(os.urandom(32))
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, key_path.name, src_dir_fd=directory, dst_dir_fd=directory)
                    os.fsync(directory)
                finally:
                    try:
                        os.unlink(temporary, dir_fd=directory)
                    except FileNotFoundError:
                        pass
                descriptor = os.open(key_path.name, flags, dir_fd=directory)
            try:
                metadata = os.fstat(descriptor)
                require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.getuid()
                        and stat.S_IMODE(metadata.st_mode) == 0o600 and metadata.st_nlink == 1,
                        "Credential key must be a private regular file owned by the current user")
                require(metadata.st_size == 32, "Invalid credential key length")
                key = os.read(descriptor, 33)
                require(len(key) == 32, "Invalid credential key length")
                return key
            finally:
                os.close(descriptor)
        finally:
            os.close(directory)

    def authorization_context(self, downstream_auth=None):
        require(self._locked and self.data is not None, "Authorization context requires the state lock")
        profile = self.data.get("profile")
        credentials = {}
        authentications = {role: (profile or {}).get(role) or {} for role in ("clientAuth", "adminAuth")}
        if downstream_auth is not None:
            authentications["downstreamAuth"] = downstream_auth
        for role, authentication in authentications.items():
            for field, reference in authentication.items():
                if field.endswith("Env"):
                    require(isinstance(reference, str), "Credential references must be environment names")
                    credentials.setdefault(role, {})[field] = {"reference": reference,
                                                               "value": os.environ.get(reference)}
            if authentication.get("source") == "keychain" and authentication.get("credentialRef"):
                ref = authentication["credentialRef"]
                try:
                    require(self.credential_reader is not None, "Keychain reader unavailable", "secure_store_unavailable")
                    current = {"value": self.credential_reader(ref)}
                except PluginError as exc:
                    current = {"error": exc.kind}
                except OSError:
                    current = {"error": "credential_store"}
                credentials.setdefault(role, {})["keychain"] = {"reference": ref, **current}
        fingerprint = None
        if credentials:
            payload = json.dumps(credentials, sort_keys=True, separators=(",", ":")).encode()
            fingerprint = hmac.new(self._credential_key(), payload, hashlib.sha256).hexdigest()
        if downstream_auth is not None:
            return digest({"downstreamAuth": downstream_auth, "credentialFingerprint": fingerprint})
        return digest({"profile": profile, "configurationRevision": self.data.get("configurationRevision", 0),
                       "credentialFingerprint": fingerprint})

    def artifact(self, identifier, suffix=".zip"):
        require(len(identifier) == 32 and all(c in "0123456789abcdef" for c in identifier), "Invalid artifact ID")
        return safe_path(self.root / "artifacts" / (identifier + suffix))

    def operation(self, action, target):
        identifier = new_id()
        self.data["operations"][identifier] = {"id": identifier, "action": action, "target": target, "status": "running",
                                              "context": digest(self.data["profile"]), "createdAt": time.time()}
        self.save()
        return self.data["operations"][identifier]
