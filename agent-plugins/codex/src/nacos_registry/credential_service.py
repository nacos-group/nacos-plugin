# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Private page credential transactions; never exposed as a plaintext MCP tool."""
import json

from .credentials import binding, reference, validate_secret
from .errors import PluginError, require
from .store import digest, new_id


def references(profile):
    return {profile.get(s + "Auth", {}).get("credentialRef") for s in ("client", "admin")
            if profile and profile.get(s + "Auth", {}).get("source") == "local"} - {None}


class CredentialMixin:
    def resolve_credentials(self, profile, surface):
        ref = profile[surface + "Auth"].get("credentialRef")
        require(ref, "Enter credentials in Settings", "credential_missing")
        value = self.vault.get(reference(ref))
        require(isinstance(value, dict) and value.get("binding") == binding(profile, surface)
                and surface in value.get("surfaces", []), "Credential does not belong to this connection", "credential_scope")
        return validate_secret(profile[surface + "Auth"]["type"], value.get("secret"))

    def validate_references(self, profile, created=()):
        previous = self.data["profile"]
        for surface in ("client", "admin"):
            auth = profile[surface + "Auth"]
            ref = auth.get("credentialRef")
            if auth.get("source") != "local" or not ref or ref in created: continue
            require(previous and previous.get(surface + "Auth", {}).get("credentialRef") == ref
                    and binding(previous, surface) == binding(profile, surface),
                    "Target or identity changed; enter credentials again for this connection", "credential_scope")

    def cleanup_credentials(self):
        pending = self.data.get("credentialGarbage", [])
        kept = []
        for ref in pending:
            if ref in references(self.data["profile"]): continue
            try: self.vault.delete(reference(ref))
            except (PluginError, OSError): kept.append(ref)
        if kept != pending:
            self.data["credentialGarbage"] = kept
            self.store.save()
        return bool(kept)

    def configure_credentials(self, profile, changes, expected_context):
        """Called only after the encrypted page request passes the one-use key check."""
        with self.store.locked():
            require(expected_context == digest(self.data["profile"]), "Connection changed; refresh Settings before saving", "conflict")
            require(self.vault.capabilities()["available"], "System credential storage is unavailable", "secure_store_unavailable")
            require(isinstance(changes, dict) and set(changes) <= {"client", "admin"}, "Invalid credential changes")
            p = self.validate_profile(profile)
            # Validate every change and every retained reference before touching Keychain.
            for surface, change in changes.items():
                auth = p[surface + "Auth"]
                require(auth.get("source") == "local" and isinstance(change, dict), "Invalid credential change")
                if change == {"clear": True}:
                    auth.pop("credentialRef", None)
                else:
                    validate_secret(auth["type"], change)
                    auth.pop("credentialRef", None)
            self.validate_references(p)
            created, grouped = [], {}
            try:
                for surface, change in changes.items():
                    if change == {"clear": True}: continue
                    key = digest({"binding": binding(p, surface), "secret": change})
                    grouped.setdefault(key, []).append(surface)
                for surfaces in grouped.values():
                    first, ref = surfaces[0], new_id()
                    # Journal references before creating them; an interrupted save can be cleaned up.
                    self.data.setdefault("credentialGarbage", []).append(ref)
                    self.store.save()
                    self.vault.put(ref, {"binding": binding(p, first), "surfaces": surfaces, "secret": changes[first]})
                    created.append(ref)
                    for surface in surfaces: p[surface + "Auth"]["credentialRef"] = ref
                return self.persist_profile(p, created)
            except Exception:
                # A state write may have succeeded before fsync reported failure. Never delete
                # a credential referenced by the durable profile. The journal is retried later.
                try:
                    durable = json.loads(self.store.file.read_text()) if self.store.file.exists() else self.data
                    live = references(durable.get("profile"))
                    for ref in created:
                        if ref not in live: self.vault.delete(ref)
                except (PluginError, OSError, ValueError): pass
                raise

    def credential_status(self):
        p = self.data["profile"] or {}
        return {surface: {"source": p.get(surface + "Auth", {}).get("source", "environment"),
                          "saved": bool(p.get(surface + "Auth", {}).get("credentialRef"))}
                for surface in ("client", "admin")}
