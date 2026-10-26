# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Secure credential contracts using synthetic values, no Keychain or GUI access."""
import copy
import ctypes as C
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from nacos_registry.credentials import DIALOG, OSASCRIPT, Keychain, NativePrompt, binding, validate_secret
from nacos_registry.errors import PluginError
from nacos_registry.store import Store
from nacos_qoder.server import call_tool, serve, tools_list
from nacos_qoder.service import Service


USER = "synthetic-user-only"
PASSWORD = 'synthetic-password-only\n"quoted" 雪'
TOKEN = 'synthetic-token-only\n\'quoted\' λ'
VALUES = {"login": {"username": USER, "password": PASSWORD}, "token": {"token": TOKEN}}


def refs(profile):
    return {(profile or {}).get(surface + "Auth", {}).get("credentialRef")
            for surface in ("client", "admin")} - {None}


class FakeVault:
    def __init__(self):
        self.entries = {}
        self.calls = []
        self.available = True
        self.fail = {}
        self.after_put = None
        self.before_delete = None

    def capabilities(self):
        return {"available": self.available, "backend": "macos-keychain" if self.available else None,
                "reason": None if self.available else "secure_store_unavailable"}

    def check(self, action):
        if not self.available:
            raise PluginError("secure_store_unavailable", "Synthetic unavailable vault")
        if action in self.fail:
            raise PluginError(self.fail[action], "Synthetic denied vault operation")

    def put(self, ref, payload):
        self.calls.append(("put", ref))
        self.check("put")
        self.entries[ref] = copy.deepcopy(payload)
        if self.after_put:
            self.after_put(ref)

    def get(self, ref):
        self.calls.append(("get", ref))
        self.check("get")
        if ref not in self.entries:
            raise PluginError("credential_missing", "Synthetic missing entry")
        return copy.deepcopy(self.entries[ref])

    def delete(self, ref):
        self.calls.append(("delete", ref))
        if self.before_delete:
            self.before_delete(ref)
        self.check("delete")
        self.entries.pop(ref, None)


class FakePrompt:
    def __init__(self):
        self.available = True
        self.calls = []
        self.error = None
        self.value = None
        self.during = None

    def capabilities(self):
        return {"available": self.available, "backend": "macos-dialog" if self.available else None,
                "reason": None if self.available else "secure_input_unavailable"}

    def collect(self, kind, label, url):
        self.calls.append((kind, label, url))
        if self.during:
            self.during()
        if self.error:
            raise self.error
        return copy.deepcopy(self.value if self.value is not None else VALUES[kind])


class CredentialTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.enterContext(patch.dict(os.environ, {"HOME": str(self.root / "home")}, clear=True))
        self.enterContext(patch("nacos_qoder.host.Path.home", return_value=self.root / "home"))
        self.enterContext(patch("nacos_qoder.host.socket.gethostname", return_value="synthetic-host"))
        self.enterContext(patch("nacos_qoder.host.getpass.getuser", return_value="synthetic-user"))
        self.enterContext(patch("nacos_registry.credentials.C.CDLL", side_effect=AssertionError("No real Keychain")))
        self.enterContext(patch("nacos_registry.credentials.subprocess.run", side_effect=AssertionError("No real GUI")))
        self.http = self.enterContext(patch("nacos_registry.registry.http", side_effect=AssertionError("No network")))
        self.enterContext(patch("nacos_registry.downstream.http", side_effect=AssertionError("No network")))
        self.vault, self.prompt = FakeVault(), FakePrompt()
        self.service = Service(Store(self.root / "state"), vault=self.vault, prompt=self.prompt)
        self.base = {"id": "synthetic-profile", "identityId": "synthetic-identity", "namespaceId": "public",
                     "clientUrl": "https://registry.example.org/nacos", "adminMode": "shared",
                     "clientAuth": {"type": "login", "source": "keychain"},
                     "allowedOperations": ["read"], "scanRoots": [], "installRoots": []}
        self.configure(self.base)

    def status(self):
        return self.service.invoke("status")

    def configure(self, profile):
        return self.service.invoke("configure", {"profile": profile,
                                   "expectedRevision": self.status()["configurationRevision"]})

    def credentials(self, action="enter", surface="client", context=None):
        return call_tool(self.service, "nacos_credentials", {
            "action": action, "surface": surface,
            "_context": self.status()["context"] if context is None else context})["structuredContent"]

    def durable(self):
        return json.loads(self.service.store.file.read_text())

    def resolve(self, surface="client"):
        with self.service.store.locked():
            return self.service.resolve_credentials(surface)

    def assert_error(self, kind, action):
        with self.assertRaises(PluginError) as caught:
            action()
        self.assertEqual(caught.exception.kind, kind)
        return caught.exception

    def assert_no_secrets(self, *outputs):
        text = json.dumps(outputs, ensure_ascii=False)
        for value in (USER, PASSWORD, TOKEN):
            self.assertNotIn(value, text)
            self.assertNotIn(json.dumps(value, ensure_ascii=False)[1:-1], text)
            for path in self.service.store.root.rglob("*"):
                if path.is_file():
                    self.assertNotIn(value.encode(), path.read_bytes(), str(path))
                    self.assertNotIn(json.dumps(value, ensure_ascii=False)[1:-1].encode(), path.read_bytes(), str(path))

    def puts(self):
        return [ref for action, ref in self.vault.calls if action == "put"]

    def reject_referenced_delete(self, ref):
        self.assertNotIn(ref, refs(self.durable()["profile"]), "Read durable profile before deleting a vault entry")

    def test_tool_contract_has_only_nonsecret_intent_and_required_context(self):
        tool = next(tool for tool in tools_list() if tool["name"] == "nacos_credentials")
        schema = tool["inputSchema"]
        self.assertEqual(set(schema["properties"]), {"action", "surface", "_context"})
        self.assertEqual(set(schema["required"]), {"action", "surface", "_context"})
        self.assertEqual(schema["properties"]["action"]["enum"], ["enter", "clear"])
        self.assertEqual(schema["properties"]["surface"]["enum"], ["client", "admin"])
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(tool["annotations"]["openWorldHint"])
        self.assertFalse(tool["annotations"]["readOnlyHint"])
        self.assertNotIn("nacos_credentials_save", {tool["name"] for tool in tools_list()})

    def test_tool_rejects_secret_arguments_and_invalid_intent_without_prompt(self):
        arguments = {"action": "enter", "surface": "client", "_context": self.status()["context"]}
        before = self.service.store.file.read_bytes()
        cases = [{**arguments, field: TOKEN} for field in ("value", "secret", "username", "password", "token", "credentialRef")]
        cases += [{key: value for key, value in arguments.items() if key != missing}
                  for missing in ("action", "surface", "_context")]
        cases += [{**arguments, "action": "save"}, {**arguments, "surface": "other"}, {**arguments, "_context": None}]
        for args in cases:
            with self.subTest(fields=list(args)):
                self.assert_error("validation", lambda: call_tool(self.service, "nacos_credentials", args))
                self.assertEqual(self.service.store.file.read_bytes(), before)
        self.assertEqual(self.prompt.calls, [])
        self.assertEqual(self.puts(), [])

    def test_keychain_profile_forbids_foreign_reference_injection(self):
        self.credentials()
        owned = refs(self.durable()["profile"])
        foreign = "f" * 32
        self.vault.entries[foreign] = {"binding": {"profileId": "foreign"}, "secret": VALUES["login"]}
        before = self.service.store.file.read_bytes()
        for surface in ("client", "admin"):
            for use_tool in (False, True):
                with self.subTest(surface=surface, use_tool=use_tool):
                    profile = {surface + "Auth": {"type": "login", "source": "keychain", "credentialRef": foreign}}
                    args = {"profile": profile, "expectedRevision": self.status()["configurationRevision"]}
                    action = (lambda: call_tool(self.service, "nacos_configure", args)) if use_tool else (lambda: self.service.invoke("configure", args))
                    self.assert_error("validation", action)
                    self.assertEqual(self.service.store.file.read_bytes(), before)
                    self.assertEqual(refs(self.durable()["profile"]), owned)
                    self.assertIn(foreign, self.vault.entries)
        self.assertNotIn(("delete", foreign), self.vault.calls)

    def test_keychain_auth_accepts_login_token_but_not_none_or_inline_fields(self):
        for kind in ("login", "token"):
            with self.subTest(kind=kind):
                result = self.configure({"clientAuth": {"type": kind, "source": "keychain"}})
                self.assertEqual(result["profile"]["clientAuth"], {"type": kind, "source": "keychain"})
        before = self.service.store.file.read_bytes()
        for auth in ({"type": "none", "source": "keychain"},
                     {"type": "token", "source": "keychain", "token": TOKEN},
                     {"type": "login", "source": "keychain", "passwordEnv": "SYNTHETIC_PASSWORD"}):
            with self.subTest(fields=list(auth)):
                self.assert_error("validation", lambda: self.configure({"clientAuth": auth}))
                self.assertEqual(self.service.store.file.read_bytes(), before)

    def test_profile_is_durable_and_lock_released_before_prompt(self):
        def during():
            self.assertFalse(self.service.store._locked)
            profile = self.durable()["profile"]
            self.assertEqual(profile["clientAuth"], {"type": "login", "source": "keychain"})
            self.assertFalse(refs(profile))
            self.assertEqual(self.puts(), [])
        self.prompt.during = during
        self.credentials()
        self.assertEqual(len(self.prompt.calls), 1)
        self.assertEqual(self.prompt.calls[0][0::2], ("login", self.base["clientUrl"]))

    def test_unsaved_profile_is_rejected_before_prompt(self):
        empty = Service(Store(self.root / "empty"), vault=self.vault, prompt=self.prompt)
        context = empty.invoke("status")["context"]
        self.assert_error("configuration", lambda: empty.invoke("credentials", {"action": "enter", "surface": "client"}, context))
        self.assertEqual(self.prompt.calls, [])
        self.assertEqual(self.puts(), [])

    def test_shared_save_is_one_scoped_entry_and_reload_uses_same_vault(self):
        result = self.credentials(surface="admin")
        profile = self.durable()["profile"]
        self.assertEqual(len(refs(profile)), 1)
        ref = profile["clientAuth"]["credentialRef"]
        self.assertEqual(profile["adminAuth"]["credentialRef"], ref)
        self.assertRegex(ref, r"^[0-9a-f]{32}$")
        self.assertEqual(self.vault.entries[ref], {"binding": binding(profile, "client"), "secret": VALUES["login"]})
        self.assertEqual(binding(profile, "client"), binding(profile, "admin"))
        self.assertEqual(binding(profile, "client")["purpose"], "shared")
        context = self.status()["context"]
        reloaded = Service(Store(self.service.store.root), vault=self.vault, prompt=FakePrompt())
        self.assertEqual(reloaded.invoke("status")["context"], context)
        with reloaded.store.locked():
            for surface in ("client", "admin"):
                self.assertEqual(reloaded.resolve_credentials(surface), VALUES["login"])
        self.assert_no_secrets(result, reloaded.invoke("status"))
        self.assertEqual(result["surfaces"], ["client", "admin"])
        self.assertFalse(result["restartRequired"])
        self.assertEqual(result["status"], "saved")

    def test_independent_entries_do_not_share_even_at_same_target(self):
        self.configure({"adminMode": "independent", "adminAuth": {"type": "token", "source": "keychain"}})
        client = self.credentials()
        admin = self.credentials(surface="admin")
        profile = self.durable()["profile"]
        self.assertEqual(len(refs(profile)), 2)
        for surface in ("client", "admin"):
            self.assertEqual(self.vault.entries[profile[surface + "Auth"]["credentialRef"]]["binding"]["purpose"], surface)
        self.assertEqual(self.resolve("client"), VALUES["login"])
        self.assertEqual(self.resolve("admin"), VALUES["token"])
        old_client = profile["clientAuth"]["credentialRef"]
        cleared = self.credentials("clear", "admin")
        self.assertEqual(refs(self.durable()["profile"]), {old_client})
        self.assertEqual(set(self.vault.entries), {old_client})
        self.assertEqual(self.status()["credentialStatus"]["admin"]["status"], "missing")
        self.assert_no_secrets(client, admin, cleared, self.status())
        self.assertEqual((client["status"], admin["status"], cleared["status"]), ("saved", "saved", "cleared"))

    def test_replace_and_shared_clear_delete_old_entries_and_change_context(self):
        first = self.credentials()
        old = next(iter(refs(self.durable()["profile"])))
        first_context = self.status()["context"]
        self.prompt.value = {"username": USER, "password": PASSWORD + "-replacement"}
        second = self.credentials(surface="admin")
        new = next(iter(refs(self.durable()["profile"])))
        self.assertNotEqual(old, new)
        self.assertEqual(set(self.vault.entries), {new})
        self.assertNotEqual(self.status()["context"], first_context)
        second_context = self.status()["context"]
        cleared = self.credentials("clear")
        self.assertEqual(refs(self.durable()["profile"]), set())
        self.assertEqual(self.vault.entries, {})
        self.assertNotEqual(self.status()["context"], second_context)
        self.assertEqual(self.durable().get("credentialGarbage", []), [])
        self.assert_no_secrets(first, second, cleared, self.status())
        self.assertEqual((first["status"], second["status"], cleared["status"]), ("saved", "saved", "cleared"))

    def test_cancel_timeout_empty_leave_profile_and_old_credential_untouched(self):
        for existing in (False, True):
            if existing:
                self.credentials()
            for kind in ("cancelled", "timed_out", "empty"):
                with self.subTest(existing=existing, kind=kind):
                    before = self.service.store.file.read_bytes()
                    entries = copy.deepcopy(self.vault.entries)
                    puts = self.puts()
                    self.prompt.error = PluginError(kind, "Synthetic entry aborted")
                    result = self.credentials()
                    self.assertEqual(result["status"], kind)
                    self.assertFalse(result["saved"])
                    self.assertEqual(self.service.store.file.read_bytes(), before)
                    self.assertEqual(self.vault.entries, entries)
                    self.assertEqual(self.puts(), puts)
                    self.assert_no_secrets(result)
            self.prompt.error = None

    def test_invalid_collected_values_never_create_entry(self):
        before = self.service.store.file.read_bytes()
        for value in ({"username": USER, "password": ""}, {"username": USER},
                      {"username": USER, "password": "bad\x00value"}):
            with self.subTest(fields=list(value)):
                self.prompt.value = value
                self.assert_error("validation", lambda: self.credentials())
                self.assertEqual(self.puts(), [])
                self.assertEqual(self.service.store.file.read_bytes(), before)

    def test_denied_put_preserves_old_entry_and_cleans_new_journal_immediately(self):
        self.credentials()
        before = self.durable()
        entries = copy.deepcopy(self.vault.entries)
        self.vault.fail["put"] = "credential_store"
        self.vault.before_delete = self.reject_referenced_delete
        self.assert_error("credential_store", lambda: self.credentials())
        new = self.puts()[-1]
        self.assertEqual(self.durable()["profile"], before["profile"])
        self.assertEqual(self.vault.entries, entries)
        self.assertIn(("delete", new), self.vault.calls)
        # Rollback may retain the durable journal; a later save must retry it.
        self.configure({"displayName": "Retry denied-put cleanup"})
        self.assertNotIn(new, self.durable().get("credentialGarbage", []))
        self.assertEqual(self.vault.entries, entries)

    def test_unavailable_vault_or_prompt_fails_before_dialog_with_environment_fallback(self):
        before = self.service.store.file.read_bytes()
        for component in (self.vault, self.prompt):
            with self.subTest(component=type(component).__name__):
                component.available = False
                try:
                    storage = self.status()["credentialStorage"]
                    self.assertFalse(storage["available"])
                    self.assertNotEqual(storage["recommendedSource"], "keychain")
                    self.assertEqual(storage["fallbackSource"], "environment")
                    self.assert_error("secure_store_unavailable", lambda: self.credentials())
                    self.assertEqual(self.prompt.calls, [])
                    self.assertEqual(self.puts(), [])
                    self.assertEqual(self.service.store.file.read_bytes(), before)
                finally:
                    component.available = True

    def test_environment_is_advanced_fallback_not_a_dialog_or_plaintext_profile(self):
        self.configure({"clientAuth": {"type": "token", "source": "environment", "tokenEnv": "SYNTHETIC_TOKEN"}})
        with patch.dict(os.environ, {"SYNTHETIC_TOKEN": TOKEN}):
            status = self.status()
            self.assertEqual(status["credentialStatus"]["client"]["source"], "environment")
            self.assertEqual(self.resolve(), VALUES["token"])
            self.assert_error("configuration", lambda: self.credentials())
            self.assert_no_secrets(status)
        self.assertEqual(self.prompt.calls, [])
        self.assertEqual(self.vault.entries, {})

    def test_unsaved_login_and_token_never_downgrade_to_anonymous(self):
        for kind in ("login", "token"):
            with self.subTest(kind=kind):
                self.configure({"clientAuth": {"type": kind, "source": "keychain"}})
                for surface in ("client", "admin"):
                    readiness = self.status()["credentialStatus"][surface]
                    self.assertFalse(readiness["saved"])
                    self.assertEqual(readiness["status"], "missing")
                    self.assert_error("credential_missing", lambda: self.resolve(surface))
                self.assert_error("credential_missing", lambda: self.service.invoke("search"))
                self.http.assert_not_called()

    def test_prompt_denial_preserves_profile_and_old_entry(self):
        self.credentials()
        before = self.service.store.file.read_bytes()
        entries, puts = copy.deepcopy(self.vault.entries), self.puts()
        self.prompt.error = PluginError("secure_input_unavailable", "Synthetic dialog denied")
        error = self.assert_error("secure_input_unavailable", lambda: self.credentials())
        self.assertEqual(self.service.store.file.read_bytes(), before)
        self.assertEqual(self.vault.entries, entries)
        self.assertEqual(self.puts(), puts)
        self.assert_no_secrets(error.result())

    def test_missing_denied_unavailable_credentials_never_send_anonymous_requests(self):
        self.credentials()
        ref = next(iter(refs(self.durable()["profile"])))
        payload = copy.deepcopy(self.vault.entries[ref])
        for condition, expected_status, kind in (("missing", "missing", "credential_missing"),
                                                  ("denied", "denied", "credential_store"),
                                                  ("unavailable", "unavailable", "secure_store_unavailable")):
            with self.subTest(condition=condition):
                self.vault.entries[ref] = copy.deepcopy(payload)
                self.vault.fail.clear()
                self.vault.available = True
                if condition == "missing":
                    del self.vault.entries[ref]
                elif condition == "denied":
                    self.vault.fail["get"] = kind
                else:
                    self.vault.available = False
                status = self.status()
                for surface in ("client", "admin"):
                    self.assertEqual(status["credentialStatus"][surface]["status"], expected_status)
                    self.assert_error(kind, lambda: self.resolve(surface))
                self.assert_error(kind, lambda: self.service.invoke("search"))
                self.http.assert_not_called()
                self.assert_no_secrets(status)

    def test_payload_binding_checks_profile_identity_target_type_and_purpose(self):
        self.credentials()
        profile = self.durable()["profile"]
        ref = next(iter(refs(profile)))
        payload = copy.deepcopy(self.vault.entries[ref])
        changes = {"profileId": "other-profile", "identityId": "other-identity", "url": "https://other.example.org/nacos",
                   "type": "token", "purpose": "client"}
        for field, value in changes.items():
            with self.subTest(field=field):
                self.vault.entries[ref] = copy.deepcopy(payload)
                self.vault.entries[ref]["binding"][field] = value
                self.assertEqual(self.status()["credentialStatus"]["client"]["status"], "reenter")
                self.assert_error("credential_scope", lambda: self.resolve())
                self.assert_error("credential_scope", lambda: self.service.invoke("search"))
                self.http.assert_not_called()

    def test_binding_config_changes_discard_refs_and_cleanup_old_entry(self):
        changes = [{"id": "other-profile"}, {"identityId": "other-identity"},
                   {"clientUrl": "https://other.example.org/nacos"},
                   {"clientAuth": {"type": "token", "source": "keychain"}},
                   {"adminMode": "independent"},
                   {"clientAuth": {"type": "token", "source": "environment", "tokenEnv": "SYNTHETIC_TOKEN"}}]
        for change in changes:
            with self.subTest(change=change):
                self.configure(self.base)
                self.credentials()
                old = next(iter(refs(self.durable()["profile"])))
                self.vault.before_delete = self.reject_referenced_delete
                result = self.configure(change)
                self.assertFalse(refs(result["profile"]))
                self.assertNotIn(old, self.vault.entries)
                self.assertEqual(self.durable().get("credentialGarbage", []), [])

    def test_nonbinding_edits_preserve_owned_refs_and_independent_target_keeps_other_surface(self):
        self.configure({"adminMode": "independent", "adminAuth": {"type": "token", "source": "keychain"}})
        self.credentials()
        self.credentials(surface="admin")
        before = self.durable()["profile"]
        self.configure({"displayName": "Renamed synthetic profile", "namespaceId": "other-namespace"})
        self.assertEqual(refs(self.durable()["profile"]), refs(before))
        self.configure({"clientUrl": "https://other.example.org/nacos"})
        after = self.durable()["profile"]
        self.assertNotIn("credentialRef", after["clientAuth"])
        self.assertEqual(after["adminAuth"], before["adminAuth"])
        self.assertEqual(set(self.vault.entries), {before["adminAuth"]["credentialRef"]})
        self.assertEqual(self.resolve("admin"), VALUES["token"])

    def test_other_state_root_has_no_access_to_same_opaque_ref(self):
        self.credentials()
        other = Service(Store(self.root / "other-state"), vault=FakeVault(), prompt=FakePrompt())
        with other.store.locked():
            other.store.data.update(copy.deepcopy(self.durable()))
            other.store.save()
        self.assertEqual(other.invoke("status")["credentialStatus"]["client"]["status"], "missing")
        with other.store.locked():
            self.assert_error("credential_missing", lambda: other.resolve_credentials("client"))

    def test_external_rotation_changes_context_without_config_change_or_secret_output(self):
        self.credentials()
        before = self.status()
        state = self.service.store.file.read_bytes()
        ref = next(iter(refs(before["profile"])))
        self.vault.entries[ref]["secret"]["password"] = PASSWORD + "-rotated"
        after = self.status()
        self.assertEqual(after["profile"], before["profile"])
        self.assertEqual(after["configurationRevision"], before["configurationRevision"])
        self.assertEqual(self.service.store.file.read_bytes(), state)
        self.assertRegex(after["context"], r"^[0-9a-f]{64}$")
        self.assert_no_secrets(before, after)
        self.assertNotEqual(after["context"], before["context"], "Current vault payload must participate in authorization context")

    def test_external_deletion_and_denial_change_context(self):
        self.credentials()
        ready = self.status()
        ref = next(iter(refs(ready["profile"])))
        payload = self.vault.entries.pop(ref)
        missing = self.status()
        self.assertNotEqual(ready["context"], missing["context"], "Deletion must invalidate prior authorization")
        self.vault.entries[ref] = payload
        self.assertEqual(self.status()["context"], ready["context"])
        self.vault.fail["get"] = "credential_store"
        denied = self.status()
        self.assertNotEqual(ready["context"], denied["context"], "Denial must invalidate prior authorization")
        self.assertNotEqual(missing["context"], denied["context"])

    def test_stale_config_context_is_rejected_before_prompt(self):
        old = self.status()["context"]
        self.configure({"displayName": "Changed before prompt"})
        before = self.service.store.file.read_bytes()
        self.assert_error("conflict", lambda: self.credentials(context=old))
        self.assertEqual(self.prompt.calls, [])
        self.assertEqual(self.puts(), [])
        self.assertEqual(self.service.store.file.read_bytes(), before)

    def test_rotated_credential_context_is_rejected_before_prompt(self):
        self.credentials()
        old = self.status()["context"]
        ref = next(iter(refs(self.durable()["profile"])))
        self.vault.entries[ref]["secret"]["password"] += "-rotated"
        calls, puts = len(self.prompt.calls), self.puts()
        self.assert_error("conflict", lambda: self.credentials(context=old))
        self.assertEqual(len(self.prompt.calls), calls)
        self.assertEqual(self.puts(), puts)

    def test_deleted_credential_stale_context_cannot_enter_or_clear(self):
        self.credentials()
        context = self.status()["context"]
        ref = next(iter(refs(self.durable()["profile"])))
        del self.vault.entries[ref]
        before, calls, puts = self.service.store.file.read_bytes(), len(self.prompt.calls), self.puts()
        for action in ("enter", "clear"):
            with self.subTest(action=action):
                self.assert_error("conflict", lambda: self.credentials(action, context=context))
                self.assertEqual(self.service.store.file.read_bytes(), before)
                self.assertEqual(len(self.prompt.calls), calls)
                self.assertEqual(self.puts(), puts)

    def test_target_or_config_change_during_prompt_is_rejected_before_put(self):
        for change in ({"clientUrl": "https://changed.example.org/nacos"}, {"displayName": "Changed during prompt"}):
            with self.subTest(change=change):
                context = self.status()["context"]
                puts = self.puts()
                captured = {}
                def during():
                    self.assertFalse(self.service.store._locked)
                    concurrent = Service(Store(self.service.store.root), vault=self.vault, prompt=FakePrompt())
                    concurrent.invoke("configure", {"profile": change,
                                      "expectedRevision": concurrent.invoke("status")["configurationRevision"]})
                    captured["state"] = self.service.store.file.read_bytes()
                self.prompt.during = during
                self.assert_error("conflict", lambda: self.credentials(context=context))
                self.assertEqual(self.puts(), puts)
                self.assertEqual(self.service.store.file.read_bytes(), captured["state"])

    def test_vault_rotation_during_prompt_is_rejected_before_put(self):
        self.credentials()
        context = self.status()["context"]
        ref = next(iter(refs(self.durable()["profile"])))
        puts = self.puts()
        before = self.service.store.file.read_bytes()
        def during():
            self.vault.entries[ref]["secret"]["password"] += "-changed-during-dialog"
        self.prompt.during = during
        self.assert_error("conflict", lambda: self.credentials(context=context))
        self.assertEqual(self.puts(), puts)
        self.assertEqual(self.service.store.file.read_bytes(), before)

    def test_put_error_after_creation_immediately_rolls_back_using_durable_profile(self):
        self.credentials()
        before = self.durable()
        old_entries = copy.deepcopy(self.vault.entries)
        self.vault.before_delete = self.reject_referenced_delete
        def after_put(ref):
            durable = self.durable()
            self.assertIn(ref, durable.get("credentialGarbage", []), "Journal must be durable before vault put")
            self.assertNotIn(ref, refs(durable["profile"]))
            raise PluginError("credential_store", "Synthetic put failed after creating entry")
        self.vault.after_put = after_put
        self.assert_error("credential_store", lambda: self.credentials())
        new = self.puts()[-1]
        self.assertEqual(self.durable()["profile"], before["profile"])
        self.assertEqual(self.vault.entries, old_entries, "Unreferenced new entry must be removed immediately")
        self.assertIn(("delete", new), self.vault.calls)
        self.vault.after_put = None
        self.configure({"displayName": "Retry partial-put cleanup"})
        self.assertNotIn(new, self.durable().get("credentialGarbage", []))
        self.assertEqual(self.vault.entries, old_entries)

    def test_store_save_failure_after_put_rolls_back_new_entry_not_old(self):
        self.credentials()
        before = self.durable()
        old_entries = copy.deepcopy(self.vault.entries)
        puts = len(self.puts())
        context = self.status()["context"]
        original_save = self.service.store.save
        failed = []
        def save():
            if not failed and len(self.puts()) > puts:
                failed.append(True)
                raise OSError("Synthetic profile save failure")
            return original_save()
        self.vault.before_delete = self.reject_referenced_delete
        with patch.object(self.service.store, "save", side_effect=save):
            with self.assertRaises(OSError):
                self.credentials(context=context)
        self.assertTrue(failed)
        self.assertEqual(self.durable()["profile"], before["profile"])
        self.assertEqual(self.durable()["configurationRevision"], before["configurationRevision"])
        self.assertEqual(self.vault.entries, old_entries, "Save failure must immediately remove unreferenced new entry")
        self.assertEqual(self.service.data["profile"], self.durable()["profile"])
        new = self.puts()[-1]
        self.configure({"displayName": "Retry failed-save cleanup"})
        self.assertNotIn(new, self.durable().get("credentialGarbage", []))
        self.assertEqual(self.vault.entries, old_entries)

    def test_journal_save_failure_prevents_put_and_preserves_profile(self):
        self.credentials()
        before = self.service.store.file.read_bytes()
        entries = copy.deepcopy(self.vault.entries)
        puts = self.puts()
        context = self.status()["context"]
        with patch.object(self.service.store, "save", side_effect=OSError("Synthetic journal save failure")):
            with self.assertRaises(OSError):
                self.credentials(context=context)
        self.assertEqual(self.puts(), puts)
        self.assertEqual(self.vault.entries, entries)
        self.assertEqual(self.service.store.file.read_bytes(), before)

    def test_file_fsync_failure_before_replace_rolls_back_unreferenced_new_entry(self):
        self.check_profile_fsync_failure(directory=False)

    def test_directory_fsync_failure_after_replace_preserves_durably_referenced_new_entry(self):
        self.check_profile_fsync_failure(directory=True)

    def check_profile_fsync_failure(self, directory):
        self.credentials()
        before = self.durable()
        old_refs = refs(before["profile"])
        context = self.status()["context"]
        puts = len(self.puts())
        original_fsync = os.fsync
        failed = []
        def fsync(fd):
            if not failed and len(self.puts()) > puts and stat.S_ISDIR(os.fstat(fd).st_mode) == directory:
                failed.append(True)
                raise OSError("Synthetic fsync failure")
            return original_fsync(fd)
        self.vault.before_delete = self.reject_referenced_delete
        with patch("nacos_registry.store.os.fsync", side_effect=fsync):
            with self.assertRaises(OSError):
                self.credentials(context=context)
        self.assertTrue(failed)
        durable_refs = refs(self.durable()["profile"])
        new = self.puts()[-1]
        self.assertTrue(durable_refs <= set(self.vault.entries), "Every durably referenced entry must survive rollback")
        if directory:
            self.assertEqual(durable_refs, {new})
            self.assertIn(new, self.vault.entries)
            self.assertNotIn(("delete", new), self.vault.calls)
        else:
            self.assertEqual(durable_refs, old_refs)
            self.assertNotIn(new, self.vault.entries, "Pre-replace fsync failure must immediately roll back new entry")
        self.assertEqual(self.service.data["profile"], self.durable()["profile"])
        self.configure({"displayName": "Retry fsync cleanup"})
        self.assertEqual(set(self.vault.entries), durable_refs)
        self.assertEqual(self.durable().get("credentialGarbage", []), [])

    def test_clear_save_failure_preserves_durable_old_reference_and_entry(self):
        self.credentials()
        before = self.durable()
        entries = copy.deepcopy(self.vault.entries)
        context = self.status()["context"]
        self.vault.before_delete = self.reject_referenced_delete
        original_save = self.service.store.save
        failed = []
        def save():
            if not failed and not refs(self.service.data["profile"]):
                failed.append(True)
                raise OSError("Synthetic clear save failure")
            return original_save()
        with patch.object(self.service.store, "save", side_effect=save):
            with self.assertRaises(OSError):
                self.credentials("clear", context=context)
        self.assertEqual(self.durable()["profile"], before["profile"])
        self.assertEqual(self.vault.entries, entries)
        self.assertEqual(self.service.data["profile"], self.durable()["profile"])

    def test_cleanup_journal_save_failure_preserves_committed_entry_for_retry(self):
        self.credentials()
        old = next(iter(refs(self.durable()["profile"])))
        puts = len(self.puts())
        context = self.status()["context"]
        original_save = self.service.store.save
        failed = []
        def save():
            if (not failed and len(self.puts()) > puts and old not in self.vault.entries
                    and refs(self.service.data["profile"]) == refs(self.durable()["profile"])):
                failed.append(True)
                raise OSError("Synthetic cleanup journal save failure")
            return original_save()
        self.vault.before_delete = self.reject_referenced_delete
        with patch.object(self.service.store, "save", side_effect=save):
            with self.assertRaises(OSError):
                self.credentials(context=context)
        self.assertTrue(failed)
        new = self.puts()[-1]
        self.assertEqual(refs(self.durable()["profile"]), {new})
        self.assertEqual(set(self.vault.entries), {new})
        self.assertNotIn(("delete", new), self.vault.calls)
        self.configure({"displayName": "Retry cleanup journal save"})
        self.assertEqual(set(self.vault.entries), {new})
        self.assertEqual(self.durable().get("credentialGarbage", []), [])
        self.assertEqual(self.resolve(), VALUES["login"])

    def test_failed_cleanup_is_journaled_and_retried_after_later_save(self):
        self.credentials()
        old = next(iter(refs(self.durable()["profile"])))
        self.vault.fail["delete"] = "credential_store"
        self.vault.before_delete = self.reject_referenced_delete
        result = self.credentials()
        new = next(iter(refs(self.durable()["profile"])))
        self.assertNotEqual(old, new)
        self.assertEqual(set(self.vault.entries), {old, new})
        self.assertIn(old, self.durable().get("credentialGarbage", []))
        self.assertNotIn(new, self.durable().get("credentialGarbage", []))
        self.vault.fail.clear()
        self.configure({"displayName": "Retry cleanup on save"})
        self.assertEqual(set(self.vault.entries), {new})
        self.assertEqual(self.durable().get("credentialGarbage", []), [])
        self.assertEqual(result["status"], "saved")

    def test_put_rollback_delete_denial_keeps_journal_for_retry(self):
        before = self.durable()["profile"]
        def after_put(ref):
            raise PluginError("credential_store", "Synthetic partial put")
        self.vault.after_put = after_put
        self.vault.fail["delete"] = "credential_store"
        self.assert_error("credential_store", lambda: self.credentials())
        orphan = self.puts()[-1]
        self.assertIn(orphan, self.vault.entries)
        self.assertIn(orphan, self.durable().get("credentialGarbage", []))
        self.assertEqual(self.durable()["profile"], before)
        self.vault.after_put = None
        self.vault.fail.clear()
        self.configure({"displayName": "Retry orphan cleanup"})
        self.assertNotIn(orphan, self.vault.entries)
        self.assertEqual(self.durable().get("credentialGarbage", []), [])

    def test_cleanup_never_deletes_live_owned_ref_even_if_journal_contains_it(self):
        self.credentials()
        live = next(iter(refs(self.durable()["profile"])))
        with self.service.store.locked():
            self.service.data["credentialGarbage"] = [live]
            self.service.store.save()
        self.vault.before_delete = self.reject_referenced_delete
        self.configure({"displayName": "Keep owned entry"})
        self.assertIn(live, self.vault.entries)
        self.assertNotIn(("delete", live), self.vault.calls)
        self.assertEqual(self.resolve(), VALUES["login"])
        self.assertEqual(self.durable().get("credentialGarbage", []), [])

    def test_keychain_login_diagnosis_uses_native_identity_without_environment_secrets(self):
        self.credentials()
        responses = [(200, {}, json.dumps({"accessToken": "synthetic-session", "tokenTtl": 3600}).encode()),
                     (200, {}, json.dumps({"code": 0, "data": {"items": []}}).encode())]
        with patch("nacos_registry.registry.http", side_effect=responses) as transport:
            result = self.service.invoke("diagnose")
        self.assertEqual(result["status"], "passed")
        login, search = transport.call_args_list
        from urllib.parse import parse_qs
        self.assertEqual(parse_qs(login.args[3].decode()), {"username": [USER], "password": [PASSWORD]})
        self.assertTrue(login.args[0].endswith("/v3/auth/user/login"))
        self.assertEqual(search.args[2], {"accessToken": "synthetic-session"})
        self.assertIn("namespaceId=public", search.args[0])
        self.assert_no_secrets(result, self.status())
        cleared = self.credentials("clear")
        self.assertEqual(cleared["status"], "cleared")
        self.assert_error("credential_missing", lambda: self.service.invoke("diagnose"))

    def test_keychain_secrets_cannot_be_reused_by_downstream_environment_alias(self):
        class Discovery:
            def discover(self, kind, name, version=None):
                if kind == "mcp":
                    return {"name": name, "version": "1.0.0", "protocol": "mcp-streamable", "frontendEndpoints": [
                        {"protocol": "https", "address": "tools.example.org", "port": 443, "path": "/mcp"}]}
                return {"name": name, "version": "1.0.0", "callInterfaces": [{"protocol": "a2a",
                    "protocolVersion": "0.3.0", "nativeDescriptor": {"protocolVersion": "0.3.0", "preferredTransport": "JSONRPC"},
                    "endpointSets": [{"source": "static", "endpoints": [{"transport": "JSONRPC", "uri": "https://tools.example.org/rpc"}]}]}]}
        self.configure({"allowedOperations": ["read", "install", "call"]})
        self.credentials()
        self.service.registry_factory = lambda *_: Discovery()
        with patch.dict(os.environ, {"SYNTHETIC_DOWNSTREAM": PASSWORD}):
            for kind in ("mcp", "agent"):
                with self.subTest(kind=kind):
                    self.assert_error("validation", lambda: self.service.invoke("connection_plan", {
                        "resourceType": kind, "name": "synthetic-tool", "auth": {"type": "bearer", "tokenEnv": "SYNTHETIC_DOWNSTREAM"}}))
        self.assertEqual(self.status()["connections"], [])
        self.http.assert_not_called()

    def test_protocol_results_and_raw_local_failures_never_expose_secrets(self):
        self.prompt.error = OSError(PASSWORD)
        requests = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
                        "name": "nacos_credentials", "arguments": {
                            "action": "enter", "surface": "client", "_context": self.status()["context"]}}}]
        sink = io.StringIO()
        serve(self.service, io.StringIO("".join(json.dumps(request) + "\n" for request in requests)), sink)
        result = json.loads(sink.getvalue().splitlines()[-1])["result"]
        self.assertTrue(result["isError"])
        self.assertEqual(json.loads(result["content"][0]["text"])["error"], "local_failure")
        self.assert_no_secrets(result, self.status())


class NativePromptTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, {"SYNTHETIC_TOKEN": TOKEN}, clear=True))
        self.enterContext(patch("nacos_registry.credentials.sys.platform", "darwin"))
        self.enterContext(patch("nacos_registry.credentials.os.access", return_value=True))
        self.run = self.enterContext(patch("nacos_registry.credentials.subprocess.run"))
        self.enterContext(patch("nacos_registry.credentials.C.CDLL", side_effect=AssertionError("No real Keychain")))
        self.prompt = NativePrompt(wait=30, budget=90)

    def completed(self, value, returncode=0, stderr=b""):
        return subprocess.CompletedProcess([OSASCRIPT], returncode, value, stderr)

    def assert_prompt_error(self, kind, action=None):
        with self.assertRaises(PluginError) as caught:
            (action or (lambda: self.prompt.collect("token", "Client", "https://registry.example.org/nacos")))()
        self.assertEqual(caught.exception.kind, kind)
        self.assertNotIn(TOKEN, str(caught.exception))
        self.assertNotIn(PASSWORD, str(caught.exception))

    def test_login_preserves_multiline_quotes_unicode_and_never_passes_value_in_args_or_env(self):
        password = PASSWORD + "\n"
        self.run.side_effect = [self.completed(("V" + USER + "\n").encode()),
                                self.completed(("V" + password + "\n").encode())]
        self.assertEqual(self.prompt.collect("login", "Client", "https://registry.example.org/nacos"),
                         {"username": USER, "password": password})
        self.assertEqual(self.run.call_count, 2)
        for index, call in enumerate(self.run.call_args_list):
            args, kwargs = call.args[0], call.kwargs
            self.assertEqual(args[0:2], [OSASCRIPT, "-"])
            self.assertEqual(args[3], "0" if index == 0 else "1")
            self.assertEqual(args[4], "30")
            self.assertEqual(kwargs["input"], DIALOG.encode())
            self.assertEqual(kwargs["env"], {"PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8"})
            self.assertEqual(kwargs["timeout"], 60)
            self.assertTrue(kwargs["capture_output"])
            self.assertFalse(kwargs.get("shell", False))
            for value in (USER, PASSWORD, TOKEN):
                self.assertNotIn(value, repr(args))
                self.assertNotIn(value, repr(kwargs))
                self.assertNotIn(value.encode(), kwargs["input"])

    def test_token_is_hidden_and_preserves_multiline_quotes_unicode(self):
        self.run.return_value = self.completed(("V" + TOKEN + "\n").encode())
        self.assertEqual(self.prompt.collect("token", "Admin", "https://registry.example.org/nacos"), VALUES["token"])
        self.assertEqual(self.run.call_args.args[0][3], "1")
        self.assertNotIn(TOKEN.encode(), self.run.call_args.kwargs["input"])
        self.assertNotIn("SYNTHETIC_TOKEN", self.run.call_args.kwargs["env"])

    def test_cancel_is_typed_and_does_not_leak_stderr(self):
        self.run.return_value = self.completed(b"", 1, ("execution error: -128 " + TOKEN).encode())
        self.assert_prompt_error("cancelled")

    def test_subprocess_timeout_is_typed_and_does_not_leak_partial_output(self):
        self.run.side_effect = subprocess.TimeoutExpired([OSASCRIPT], 60, output=TOKEN.encode(), stderr=PASSWORD.encode())
        self.assert_prompt_error("timed_out")

    def test_dialog_giving_up_is_timeout(self):
        self.run.return_value = self.completed(b"T\n")
        self.assert_prompt_error("timed_out")

    def test_empty_token_or_username_aborts_without_next_dialog(self):
        for kind in ("token", "login"):
            with self.subTest(kind=kind):
                self.run.reset_mock()
                self.run.return_value = self.completed(b"V\n")
                self.assert_prompt_error("empty", lambda: self.prompt.collect(kind, "Client", "https://registry.example.org/nacos"))
                self.assertEqual(self.run.call_count, 1)

    def test_empty_password_aborts_after_username_without_returning_partial_secret(self):
        self.run.side_effect = [self.completed(("V" + USER + "\n").encode()), self.completed(b"V\n")]
        self.assert_prompt_error("empty", lambda: self.prompt.collect("login", "Client", "https://registry.example.org/nacos"))
        self.assertEqual(self.run.call_count, 2)

    def test_exhausted_total_budget_stops_before_second_dialog(self):
        self.run.return_value = self.completed(("V" + USER + "\n").encode())
        with patch("nacos_registry.credentials.time.monotonic", side_effect=[0, 0, 89]):
            self.assert_prompt_error("timed_out", lambda: self.prompt.collect("login", "Client", "https://registry.example.org/nacos"))
        self.assertEqual(self.run.call_count, 1)

    def test_os_error_and_unexpected_result_fail_closed_without_raw_output(self):
        self.run.side_effect = OSError(TOKEN)
        self.assert_prompt_error("secure_input_unavailable")
        self.run.side_effect = None
        for result in (self.completed(b"", 1, TOKEN.encode()), self.completed(TOKEN.encode())):
            with self.subTest(returncode=result.returncode):
                self.run.return_value = result
                self.assert_prompt_error("secure_input_unavailable")

    def test_missing_native_executable_fails_closed_without_subprocess(self):
        with patch("nacos_registry.credentials.os.access", return_value=False):
            self.assertFalse(self.prompt.capabilities()["available"])
            self.assert_prompt_error("secure_input_unavailable")
        self.run.assert_not_called()

    def test_non_macos_platform_fails_closed_without_gui_or_framework_loading(self):
        for platform in ("linux", "win32"):
            with self.subTest(platform=platform), patch("nacos_registry.credentials.sys.platform", platform):
                self.assertFalse(self.prompt.capabilities()["available"])
                self.assert_prompt_error("secure_input_unavailable")
                vault = Keychain("/synthetic/state")
                self.assertFalse(vault.capabilities()["available"])
                for action in (lambda: vault.get("a" * 32), lambda: vault.put("a" * 32, {}), lambda: vault.delete("a" * 32)):
                    self.assert_prompt_error("secure_store_unavailable", action)
        self.run.assert_not_called()

    def test_unavailable_macos_framework_is_fail_closed_and_root_scopes_keychain_service(self):
        with patch("nacos_registry.credentials.C.CDLL", side_effect=OSError("Synthetic unavailable framework")):
            first, same, other = Keychain("/synthetic/state"), Keychain("/synthetic/state"), Keychain("/synthetic/other")
        self.assertEqual(first.service, same.service)
        self.assertNotEqual(first.service, other.service)
        self.assertFalse(first.capabilities()["available"])
        self.assert_prompt_error("secure_store_unavailable", lambda: first.get("a" * 32))
        self.run.assert_not_called()

    def test_secret_validation_uses_utf8_byte_limits_and_rejects_nul_extra_or_missing_fields(self):
        self.assertEqual(validate_secret("token", {"token": "雪" * 2730}), {"token": "雪" * 2730})
        self.assertEqual(validate_secret("login", {"username": "u" * 256, "password": "p" * 4096}),
                         {"username": "u" * 256, "password": "p" * 4096})
        cases = [("token", {"token": "雪" * 2731}), ("token", {"token": ""}), ("token", {"token": "bad\x00value"}),
                 ("token", {"token": TOKEN, "extra": TOKEN}), ("login", {"username": USER}),
                 ("login", {"username": "u" * 257, "password": PASSWORD}), ("token", {"token": 123})]
        for kind, value in cases:
            with self.subTest(kind=kind, fields=list(value)):
                self.assert_prompt_error("validation", lambda: validate_secret(kind, value))


class NativeKeychainTests(unittest.TestCase):
    def test_secitem_requests_are_scoped_non_synchronizable_and_errors_are_redacted(self):
        objects, requests, entries = {}, [], {}
        released = []

        def allocate(value):
            pointer = len(objects) + 1
            objects[pointer] = value
            return pointer

        def data(_, value, length):
            return allocate((length, C.create_string_buffer(value)))

        def query(pointer, output=None, action="get"):
            fields = copy.deepcopy(objects[pointer])
            requests.append(fields)
            key = (objects[fields["kSecAttrService"]], objects[fields["kSecAttrAccount"]])
            if action == "put":
                entries[key] = objects[fields["kSecValueData"]]
            elif key not in entries:
                return -25300
            elif action == "delete":
                del entries[key]
            else:
                output._obj.value = allocate(entries[key])
            return 0

        vault = Keychain.__new__(Keychain)
        vault.available, vault.service = True, "synthetic-qoder-service"
        vault._constant = lambda key: key
        vault.cf = SimpleNamespace(
            CFStringCreateWithCString=lambda _, value, encoding: allocate(value.decode()),
            CFDataCreate=data,
            CFDataGetLength=lambda pointer: objects[pointer.value][0],
            CFDataGetBytePtr=lambda pointer: C.addressof(objects[pointer.value][1]),
            CFDictionaryCreateMutable=lambda *args: allocate({}),
            CFDictionarySetValue=lambda pointer, key, value: objects[pointer].__setitem__(key, value),
            CFRelease=released.append)
        vault.sec = SimpleNamespace(
            SecItemAdd=lambda pointer, output: query(pointer, output, "put"),
            SecItemCopyMatching=query,
            SecItemDelete=lambda pointer: query(pointer, action="delete"))
        ref, payload = "a" * 32, {"binding": {"purpose": "client"}, "secret": VALUES["token"]}
        vault.put(ref, payload)
        self.assertEqual(vault.get(ref), payload)
        vault.delete(ref)
        vault.delete(ref)
        self.assertEqual(entries, {})
        for fields in requests:
            self.assertEqual(fields["kSecClass"], "kSecClassGenericPassword")
            self.assertEqual(fields["kSecAttrSynchronizable"], "kCFBooleanFalse")
            self.assertEqual(objects[fields["kSecAttrService"]], vault.service)
            self.assertEqual(objects[fields["kSecAttrAccount"]], ref)
        self.assertTrue(released)
        self.assertEqual(requests[1]["kSecReturnData"], "kCFBooleanTrue")
        self.assertEqual(requests[1]["kSecMatchLimit"], "kSecMatchLimitOne")
        with self.assertRaises(PluginError) as missing:
            vault.get(ref)
        self.assertEqual(missing.exception.kind, "credential_missing")
        vault.sec.SecItemCopyMatching = lambda *args: -25293
        with self.assertRaises(PluginError) as denied:
            vault.get(ref)
        self.assertEqual(denied.exception.kind, "credential_store")
        self.assertNotIn(TOKEN, str(denied.exception))
        before = len(requests)
        with self.assertRaises(PluginError):
            vault.delete("invalid-reference")
        self.assertEqual(len(requests), before)


if __name__ == "__main__":
    unittest.main()
