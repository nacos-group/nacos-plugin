# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nacos_registry.credentials import Keychain
from nacos_registry.errors import PluginError
from nacos_registry.registry import Registry
from nacos_registry.server import DEFINITIONS, serve, tools_list, validate
from nacos_registry.service import Service
from nacos_registry.store import Store, digest


class MemoryVault:
    def __init__(self): self.items = {}; self.failure = None; self.delete_failure = False
    def capabilities(self): return {"available": True, "backend": "test-only"}
    def put(self, ref, value):
        if self.failure: raise PluginError("credential_store", "Denied")
        self.items[ref] = copy.deepcopy(value)
    def get(self, ref):
        if ref not in self.items: raise PluginError("credential_missing", "Missing")
        return copy.deepcopy(self.items[ref])
    def delete(self, ref):
        if self.delete_failure: raise PluginError("credential_store", "Denied")
        self.items.pop(ref, None)


def profile():
    return {"id": "sample", "identityId": "person", "namespaceId": "public", "allowedOperations": ["read", "develop"],
            "clientUrl": "https://registry.example.org/nacos", "adminUrl": "https://registry.example.org/nacos",
            "clientAuth": {"type": "login", "source": "local"}, "adminAuth": {"type": "login", "source": "local"}}


class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = MemoryVault(); self.service = Service(Store(self.root), vault=self.vault)
        self.secret = {"username": "synthetic-user", "password": "synthetic-secret-不可外传"}

    def status(self): return self.service.invoke("status")
    def save(self, p=None, changes=None, context=None):
        return self.service.configure_credentials(p or profile(), changes if changes is not None else {"client": self.secret, "admin": self.secret},
                                                  context or self.status()["context"])

    def test_save_reopen_no_secrets_in_state_or_public_results(self):
        result = self.save(); p = result["profile"]
        self.assertEqual(p["clientAuth"]["credentialRef"], p["adminAuth"]["credentialRef"])
        second = Service(Store(self.root), vault=self.vault)
        state = second.invoke("status")
        self.assertEqual(second.resolve_credentials(state["profile"], "client"), self.secret)
        self.assertTrue(state["credentials"]["client"]["saved"])
        for value in self.secret.values():
            self.assertNotIn(value, (self.root / "state.json").read_text())
            self.assertNotIn(value, json.dumps(result, ensure_ascii=False))
            self.assertNotIn(value, json.dumps(state, ensure_ascii=False))
        self.assertEqual(state["credentialCleanupPending"], False)

    def test_replace_clear_and_revoke_shared_credentials(self):
        p = self.save()["profile"]; ref = p["clientAuth"]["credentialRef"]
        p = self.save(p, {"client": {**self.secret, "password": "new-secret"}})["profile"]
        self.assertIn(ref, self.vault.items)  # Admin still uses it.
        self.assertNotEqual(p["clientAuth"]["credentialRef"], ref)
        p = self.save(p, {"client": {"clear": True}, "admin": {"clear": True}})["profile"]
        self.assertEqual(self.vault.items, {})
        self.assertFalse(self.status()["credentials"]["client"]["saved"])
        with self.assertRaises(PluginError): self.service.resolve_credentials(p, "client")

    def test_destination_identity_and_foreign_reference_rejected(self):
        p = self.save()["profile"]
        for key, value in [("clientUrl", "https://other.example.org"), ("id", "another"), ("identityId", "other")]:
            q = copy.deepcopy(p); q[key] = value
            with self.subTest(key=key), self.assertRaises(PluginError): self.service.invoke("configure", {"profile": q})
            with self.subTest(resolve=key), self.assertRaises(PluginError): self.service.resolve_credentials(q, "client")
        q = copy.deepcopy(p); q["clientAuth"]["credentialRef"] = "0" * 32
        with self.assertRaises(PluginError): self.service.invoke("configure", {"profile": q})
        self.assertEqual(self.status()["profile"], p)

    def test_destination_change_requires_new_secret_and_new_context(self):
        p = self.save()["profile"]; before = self.status()["context"]
        p["clientUrl"] = "https://other.example.org/nacos"
        p = self.save(p, {"client": self.secret})["profile"]
        self.assertEqual(self.service.resolve_credentials(p, "client"), self.secret)
        self.assertNotEqual(self.status()["context"], before)
        with self.assertRaises(PluginError): self.save(p, {"client": self.secret}, before)

    def test_validation_precedes_vault_mutation(self):
        for changes in ({"client": self.secret, "admin": {"password": "missing-user"}},
                        {"client": {"password": "p", "username": "u", "unexpected": True}}):
            with self.assertRaises(PluginError): self.save(changes=changes)
            self.assertFalse(self.vault.items)
        with self.assertRaises(PluginError): self.save(p={**profile(), "scanRoots": ["/"]})
        self.assertFalse(self.vault.items)

    def test_keychain_failure_preserves_original_profile(self):
        p = self.save()["profile"]; self.vault.failure = True
        with self.assertRaises(PluginError): self.save(p)
        self.assertEqual(self.status()["profile"], p)
        self.assertEqual(self.service.resolve_credentials(p, "client"), self.secret)

    def test_state_write_failure_does_not_leave_referenced_credentials_missing(self):
        p = self.save()["profile"]; before = set(self.vault.items)
        original = self.service.store.save; count = 0
        def fail_commit():
            nonlocal count
            count += 1
            if count == 2: raise OSError("synthetic write failure")
            original()
        with patch.object(self.service.store, "save", side_effect=fail_commit), self.assertRaises(OSError): self.save(p)
        self.assertEqual(set(self.vault.items), before)
        self.assertEqual(self.status()["profile"], p)

    def test_post_commit_fsync_failure_keeps_new_credential(self):
        original = self.service.store.save; count = 0
        def fail_after_commit():
            nonlocal count
            count += 1; original()
            if count == 2: raise OSError("synthetic fsync failure")
        with patch.object(self.service.store, "save", side_effect=fail_after_commit), self.assertRaises(OSError): self.save()
        p = self.status()["profile"]
        self.assertEqual(self.service.resolve_credentials(p, "client"), self.secret)

    def test_cleanup_denial_is_reported_and_retried(self):
        p = self.save()["profile"]; self.vault.delete_failure = True
        result = self.save(p, {"client": {"clear": True}, "admin": {"clear": True}})
        self.assertTrue(result["credentialCleanupPending"])
        self.assertTrue(self.vault.items)
        self.vault.delete_failure = False
        self.service.invoke("configure", {"profile": result["profile"]})
        self.assertFalse(self.status()["credentialCleanupPending"]); self.assertFalse(self.vault.items)

    def test_env_mode_and_ordinary_edits_preserve_compatibility(self):
        p = self.save()["profile"]; refs = set(self.vault.items)
        p["displayName"] = "Renamed"
        self.service.invoke("configure", {"profile": p}); self.assertEqual(set(self.vault.items), refs)
        for surface in ("client", "admin"): p[surface + "Auth"] = {"type": "token", "tokenEnv": "SAMPLE_TOKEN"}
        self.service.invoke("configure", {"profile": p}); self.assertFalse(self.vault.items)
        with patch.dict("os.environ", SAMPLE_TOKEN="synthetic-env-token"):
            self.assertEqual(Registry(p).headers("client"), {"accessToken": "synthetic-env-token"})

    def test_token_and_login_use_current_private_resolver(self):
        p = profile(); p["clientAuth"] = p["adminAuth"] = {"type": "token", "source": "local"}
        p = self.save(p, {"client": {"token": "synthetic-token"}, "admin": {"token": "synthetic-token"}})["profile"]
        self.assertEqual(Registry(p, self.service.resolve_credentials).headers("client"), {"accessToken": "synthetic-token"})
        p = self.save()["profile"]
        with patch("nacos_registry.registry.http", return_value=(200, {}, b'{"accessToken":"result","tokenTtl":100}')) as http:
            self.assertEqual(Registry(p, self.service.resolve_credentials).headers("client"), {"accessToken": "result"})
            self.assertIn(b"username=synthetic-user", http.call_args.args[3])

    def test_unsupported_platform_does_not_create_a_plaintext_store(self):
        for platform in ("linux", "win32"):
            with self.subTest(platform=platform), patch("nacos_registry.credentials.sys.platform", platform):
                vault = Keychain(self.root)
                self.assertFalse(vault.capabilities()["available"])
                with self.assertRaises(PluginError): vault.put("a" * 32, self.secret)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_public_tool_schemas_reject_secret_fields(self):
        for name, args in [("configure", {"profile": {**profile(), "password": "not-allowed"}}),
                           ("open_center_panel", {"route": "settings", "draft": {"clientAuth": {"type": "login", "password": "not-allowed"}}}),
                           ("credentials_begin", {"password": "not-allowed"}),
                           ("credentials_save", {"password": "not-allowed", "envelope": "invalid"})]:
            with self.subTest(name=name), self.assertRaises(PluginError): validate(args, DEFINITIONS[name][1])
        for name in ("nacos_credentials_begin", "nacos_credentials_save"):
            tool = next(t for t in tools_list() if t["name"] == name)
            self.assertEqual(tool["_meta"]["ui"]["visibility"], ["app"])

    def test_open_settings_returns_nonsecret_draft_without_configuring(self):
        requests = [{"id": 1, "method": "initialize", "params": {}},
                    {"id": 2, "method": "tools/call", "params": {"name": "nacos_open_center_panel", "arguments": {
                        "route": "settings", "draft": {"clientUrl": "https://registry.example.org/nacos", "clientAuth": {"type": "login", "source": "local"}}}}}]
        out = io.StringIO()
        serve(self.service, io.StringIO('\n'.join(json.dumps({"jsonrpc": "2.0", **r}) for r in requests)), out)
        result = json.loads(out.getvalue().splitlines()[1])["result"]["structuredContent"]
        self.assertEqual(result["route"], "settings"); self.assertTrue(result["launchId"])
        self.assertEqual(result["context"], digest(None)); self.assertIsNone(self.status()["profile"])


class FakeKey:
    """Channel lifecycle tests; cryptographic interoperability is tested separately."""
    def __init__(self, payload): self.payload = payload; self.closed = False
    def public_key(self): return "synthetic-public-key"
    def decrypt(self, parsed): return copy.deepcopy(self.payload)
    def close(self): self.closed = True


def envelope(kid, **headers):
    from nacos_registry.credential_crypto import b64
    return '.'.join([b64(json.dumps({"alg": "RSA-OAEP-256", "enc": "A256CBC-HS512", "kid": kid, **headers}).encode()),
                     b64(bytes(256)), b64(bytes(16)), b64(bytes(16)), b64(bytes(32))])


class ChannelTests(CredentialTests):
    def setUp(self):
        super().setUp()
        from nacos_registry.credential_channel import CredentialChannel
        self.keys = []
        def factory():
            key = FakeKey({"profile": profile(), "changes": {"client": self.secret, "admin": self.secret}})
            self.keys.append(key); return key
        self.channel = CredentialChannel(self.service, factory); self.addCleanup(self.channel.close)

    def test_encrypted_channel_one_use_and_no_public_secret(self):
        ctx = self.status()['context']; session = self.channel.begin(ctx)
        self.assertEqual(session['mode'], 'mcp-jwe-v1')
        result = self.channel.save(envelope(session['sessionId']), ctx)
        self.assertEqual(result['status'], 'configured'); self.assertTrue(self.keys[-1].closed)
        self.assertNotIn(self.secret['password'], json.dumps([session, result]))
        with self.assertRaises(PluginError): self.channel.save(envelope(session['sessionId']), ctx)
        self.assertFalse(self.channel.sessions)

    def test_expiry_and_context_reject_without_writes(self):
        ctx = self.status()['context']
        for kind in ('timeout', 'context', 'expiry'):
            session = self.channel.begin(ctx); kid = session['sessionId']
            if kind == 'timeout': self.channel.sessions[kid]['expires'] = 0
            if kind == 'expiry': self.channel.expire(kid)
            with self.assertRaises(PluginError): self.channel.save(envelope(kid), 'other' if kind == 'context' else ctx)
            self.assertTrue(self.keys[-1].closed)
            self.assertFalse(self.vault.items); self.assertIsNone(self.status()['profile'])

    def test_saved_revision_changed_after_begin_rejects(self):
        ctx = self.status()['context']; session = self.channel.begin(ctx)
        p = profile(); p['clientAuth'] = p['adminAuth'] = {'type': 'none'}
        p = self.service.invoke('configure', {'profile': p})['profile']
        with self.assertRaises(PluginError): self.channel.save(envelope(session['sessionId']), ctx)
        self.assertEqual(self.status()['profile'], p); self.assertFalse(self.vault.items)
        self.assertTrue(self.keys[-1].closed)

    def test_decrypt_failure_consumes_key_and_never_echoes_input(self):
        ctx = self.status()['context']; session = self.channel.begin(ctx)
        with patch.object(self.keys[-1], 'decrypt', side_effect=ValueError(self.secret['password'])):
            with self.assertRaises(PluginError) as raised: self.channel.save(envelope(session['sessionId']), ctx)
        self.assertNotIn(self.secret['password'], str(raised.exception))
        self.assertTrue(self.keys[-1].closed); self.assertFalse(self.vault.items)
        with self.assertRaises(PluginError): self.channel.save(envelope(session['sessionId']), ctx)

    def test_pending_keys_bounded_and_released_on_close(self):
        ctx = self.status()['context']
        for _ in range(32): self.channel.begin(ctx)
        with self.assertRaises(PluginError): self.channel.begin(ctx)
        self.channel.close()
        self.assertTrue(all(k.closed for k in self.keys)); self.assertFalse(self.channel.sessions)
        with patch('threading.Timer.start', side_effect=RuntimeError('timer failed')):
            with self.assertRaises(RuntimeError): self.channel.begin(ctx)
        self.assertTrue(self.keys[-1].closed); self.assertFalse(self.channel.sessions)


class EnvelopeTests(unittest.TestCase):
    def test_only_bounded_fixed_algorithm_compact_jwe_accepted(self):
        from nacos_registry.credential_crypto import parse
        valid = envelope('A' * 43)
        self.assertEqual(parse(valid)[0]['kid'], 'A' * 43)
        for bad in [None, {}, '', 'x' * 46001, valid + '.', valid.replace('.', '=.', 1),
                    envelope('A' * 43, alg='RSA1_5'), envelope('A' * 43, enc='A128GCM'),
                    envelope('A' * 43, jku='https://example.org/key'), envelope('bad')]:
            with self.subTest(value=str(bad)[:40]), self.assertRaises(PluginError): parse(bad)

    def test_rfc7518_b3_authentication_vector_and_tampering(self):
        from nacos_registry.credential_crypto import authenticate
        # RFC 7518 Appendix B.3, independently published A256CBC-HS512 vector.
        key = bytes(range(64)); aad = b'The second principle of Auguste Kerckhoffs'
        iv = bytes.fromhex('1af38c2dc2b96ffdd86694092341bc04')
        encrypted = bytes.fromhex(
            '4affaaadb78c31c5da4b1b590d10ffbd3dd8d5d302423526912da037ecbcc7bd'
            '822c301dd67c373bccb584ad3e9279c2e6d12a1374b77f077553df829410446b'
            '36ebd97066296ae6427ea75c2e0846a11a09ccf5370dc80bfecbad28c73f09b3'
            'a3b75e662a2594410ae496b2e2e6609e31e6e02cc837f053d21f37ff4f51950b'
            'be2638d09dd7a4930930806d0703b1f6')
        tag = bytes.fromhex('4dd3b4c088a7f45c216839645b2012bf2e6269a8c56a816dbc1b267761955bc5')
        args = [key, aad, iv, encrypted, tag]; authenticate(*args)
        for index in range(5):
            changed = args.copy(); changed[index] = bytes([args[index][0] ^ 1]) + args[index][1:]
            with self.subTest(index=index), self.assertRaises(PluginError): authenticate(*changed)


def load_tests(loader, tests, pattern):
    suite = loader.loadTestsFromTestCase(CredentialTests)
    suite.addTests(ChannelTests(name) for name in ChannelTests.__dict__ if name.startswith('test_'))
    suite.addTests(loader.loadTestsFromTestCase(EnvelopeTests))
    return suite
