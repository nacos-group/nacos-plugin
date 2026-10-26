# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Keychain-backed registry credentials; tools carry only nonsecret intent and context."""
import copy
import json
import os

from .credentials import binding, reference, validate_secret
from .errors import PluginError, require
from .store import new_id, safe_path
from .transport import secret

STATUS = {"credential_missing": "missing", "credential_scope": "reenter", "secure_store_unavailable": "unavailable"}


def credential_refs(profile):
    return {(profile or {}).get(surface + "Auth", {}).get("credentialRef") for surface in ("client", "admin")} - {None}


def without_ref(auth):
    return {key: value for key, value in auth.items() if key != "credentialRef"}


class CredentialMixin:
    def resolve_credentials(self, surface):
        profile = self.data["profile"]
        auth = profile[surface + "Auth"]
        if auth.get("source") != "keychain":
            return {field[:-3]: secret(ref) for field, ref in auth.items() if field.endswith("Env")}
        ref = auth.get("credentialRef")
        require(ref, "Credential is not saved; enter it through the native credential dialog", "credential_missing")
        value = self.vault.get(reference(ref))
        require(isinstance(value, dict) and value.get("binding") == binding(profile, surface),
                "Saved credential belongs to another connection; enter it again", "credential_scope")
        return validate_secret(auth["type"], value.get("secret"))

    def nacos_secret_values(self):
        values = set()
        for surface in ("client", "admin"):
            auth = self.data["profile"][surface + "Auth"]
            if auth.get("source") == "keychain":
                values.update(self.resolve_credentials(surface).values())
            else:
                values.update(os.environ[ref] for field, ref in auth.items() if field.endswith("Env") and os.environ.get(ref))
        return values

    def keychain_status(self, surface):
        auth = self.data["profile"][surface + "Auth"]
        result = {"type": auth["type"], "source": "keychain", "saved": bool(auth.get("credentialRef"))}
        if not result["saved"]:
            return {**result, "status": "missing"}
        try:
            self.resolve_credentials(surface)
            return {**result, "status": "ready"}
        except PluginError as exc:
            return {**result, "status": STATUS.get(exc.kind, "denied")}

    def carry_credential_refs(self, previous, profile):
        """Keep a saved entry only for the same connection, identity, target, type and purpose."""
        for surface in ("client", "admin"):
            auth = profile[surface + "Auth"]
            auth.pop("credentialRef", None)
            old = (previous or {}).get(surface + "Auth", {})
            if (auth.get("source") == "keychain" and old.get("source") == "keychain" and old.get("credentialRef")
                    and binding(previous, surface) == binding(profile, surface)):
                auth["credentialRef"] = old["credentialRef"]

    def journal_dropped_refs(self, previous, profile):
        garbage = self.data.setdefault("credentialGarbage", [])
        dropped = credential_refs(previous) - credential_refs(profile)
        garbage.extend(ref for ref in sorted(dropped) if ref not in garbage)
        owners = self.data.setdefault("credentialGarbageBindings", {})
        for surface in ("client", "admin"):
            ref = (previous or {}).get(surface + "Auth", {}).get("credentialRef")
            if ref in dropped:
                owners.setdefault(ref, binding(previous, surface))

    def cleanup_credentials(self):
        pending = self.data.get("credentialGarbage", [])
        owners = self.data.get("credentialGarbageBindings", {})
        live, kept = credential_refs(self.data["profile"]), []
        for ref in pending:
            if ref in live:
                continue
            try:
                value = self.vault.get(reference(ref))
                require(ref in owners and isinstance(value, dict) and value.get("binding") == owners[ref],
                        "Credential cleanup ownership could not be verified", "credential_scope")
                self.vault.delete(ref)
            except PluginError as exc:
                if exc.kind != "credential_missing":
                    kept.append(ref)
            except OSError:
                kept.append(ref)
        if kept != pending:
            self.data["credentialGarbage"] = kept
            self.data["credentialGarbageBindings"] = {ref: owners[ref] for ref in kept if ref in owners}
            self.store.save()
        return kept

    def credential_target(self, action, surface, expected_context):
        require(expected_context == self.store.authorization_context(),
                "Configuration or credentials changed; read status before continuing", "conflict")
        p = self.data["profile"]
        require(p is not None, "Save the connection before entering credentials", "configuration")
        auth = p[surface + "Auth"]
        require(auth.get("source") == "keychain" and auth["type"] in ("login", "token"),
                "Choose Keychain credentials for this connection before entering them", "configuration")
        if action == "enter":
            require(self.vault.capabilities()["available"] and self.prompt.capabilities()["available"],
                    "Keychain entry requires local macOS; use environment references or configure later", "secure_store_unavailable")
        surfaces = ["client", "admin"] if p["adminMode"] == "shared" else [surface]
        return auth["type"], p[surface + "Url"], surfaces

    def credentials(self, action, surface, expected_context=None):
        require(action in ("enter", "clear") and surface in ("client", "admin"), "Invalid credential request")
        require(isinstance(expected_context, str), "Read status and pass its context", "conflict")
        with self.store.locked():
            kind, url, surfaces = self.credential_target(action, surface, expected_context)
            self.cleanup_credentials()
            if action == "clear":
                return self.clear_credentials(surfaces)
        label = "Client/Admin 共用" if len(surfaces) == 2 else surface.capitalize()
        # The dialog runs outside the state lock; the target is rechecked before saving.
        try:
            value = self.prompt.collect(kind, label, url)
        except PluginError as exc:
            if exc.kind in ("cancelled", "timed_out", "empty"):
                return {"status": exc.kind, "saved": False, "message": exc.message}
            raise
        with self.store.locked():
            self.credential_target(action, surface, expected_context)
            return self.save_credentials(surfaces, value)

    def save_credentials(self, surfaces, value):
        p = copy.deepcopy(self.data["profile"])
        validate_secret(p[surfaces[0] + "Auth"]["type"], value)
        ref = new_id()
        self.data.setdefault("credentialGarbage", []).append(ref)
        self.data.setdefault("credentialGarbageBindings", {})[ref] = binding(p, surfaces[0])
        try:
            self.store.save()
            self.vault.put(ref, {"binding": binding(p, surfaces[0]), "secret": value})
            for surface in surfaces:
                p[surface + "Auth"]["credentialRef"] = ref
            result = self.persist_profile(p)
            return {**result, "status": "saved", "surfaces": surfaces, "restartRequired": False,
                    "cleanupPending": bool(self.data.get("credentialGarbage"))}
        except Exception:
            # fsync may fail after replacement; never remove an entry referenced by durable state.
            try:
                durable = json.loads(safe_path(self.store.file).read_text())
                self.store.data = durable
                if ref not in credential_refs(durable.get("profile")):
                    self.cleanup_credentials()
            except (PluginError, OSError, ValueError):
                pass
            raise

    def clear_credentials(self, surfaces):
        p = copy.deepcopy(self.data["profile"])
        if not any(p[surface + "Auth"].get("credentialRef") for surface in surfaces):
            return {"status": "not_saved", "surfaces": surfaces, "credentialStatus": self.credential_status(),
                    "cleanupPending": bool(self.data.get("credentialGarbage"))}
        for surface in surfaces:
            p[surface + "Auth"].pop("credentialRef", None)
        try:
            result = self.persist_profile(p)
        except Exception:
            try:
                self.store.data = json.loads(safe_path(self.store.file).read_text())
            except (PluginError, OSError, ValueError):
                pass
            raise
        return {**result, "status": "cleared", "surfaces": surfaces,
                "cleanupPending": bool(self.data.get("credentialGarbage"))}

    def credential_storage(self):
        store, entry = self.vault.capabilities(), self.prompt.capabilities()
        available = store["available"] and entry["available"]
        return {"available": available, "backend": store["backend"], "input": entry["backend"],
                "recommendedSource": "keychain" if available else None,
                "fallbackSource": "environment", "restartRequired": False if available else None,
                "reason": None if available else store["reason"] or entry["reason"]}
