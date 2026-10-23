# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""One-use encrypted page submissions over the supported local MCP channel.

No HTTP listener or plaintext tool argument. Each save gets an ephemeral key
that is released after use/expiry; recordings of tool arguments hold only JWE.
"""
import secrets
import threading
import time

from .credential_crypto import EphemeralKey, parse
from .errors import PluginError, require


class CredentialChannel:
    TTL = 60

    def __init__(self, service, key_factory=EphemeralKey):
        self.service, self.key_factory = service, key_factory
        self.sessions = {}
        self.lock = threading.Lock()

    def expire(self, session_id):
        with self.lock: session = self.sessions.pop(session_id, None)
        if session: session['key'].close()

    def begin(self, context):
        require(context is not None, 'Expected connection context is required')
        status = self.service.invoke('status', expected_context=context)
        require(status['credentialStorage']['available'], 'System credential storage is unavailable', 'secure_store_unavailable')
        with self.lock:
            require(len(self.sessions) < 32, 'Too many pending credential requests; try again shortly', 'busy')
            key = None; session_id = None
            try:
                key = self.key_factory(); public = key.public_key()
                session_id = secrets.token_urlsafe(32)
                timer = threading.Timer(self.TTL, self.expire, [session_id]); timer.daemon = True
                self.sessions[session_id] = {'context': context, 'expires': time.monotonic() + self.TTL, 'key': key, 'timer': timer}
                timer.start()
                return {'mode': 'mcp-jwe-v1', 'sessionId': session_id, 'publicKey': public, 'expiresIn': self.TTL}
            except Exception:
                if session_id: self.sessions.pop(session_id, None)
                if key: key.close()
                raise

    def save(self, envelope, context):
        parsed = parse(envelope)
        with self.lock: session = self.sessions.pop(parsed[0]['kid'], None)
        require(session, 'Credential form expired; save again', 'credential_session')
        session['timer'].cancel()
        try:
            require(session['expires'] > time.monotonic(), 'Credential form expired; save again', 'credential_session')
            require(context == session['context'], 'Connection changed; refresh Settings before saving', 'conflict')
            payload = session['key'].decrypt(parsed)
            require(isinstance(payload, dict) and set(payload) == {'profile', 'changes'}, 'Invalid credential request')
            return self.service.configure_credentials(payload['profile'], payload['changes'], context)
        except PluginError: raise
        except (OSError, ValueError, TypeError, KeyError, UnicodeError, AttributeError, RecursionError):
            raise PluginError('credential_envelope', 'Credential save could not be confirmed; reload saved settings') from None
        finally: session['key'].close()

    def close(self):
        with self.lock: sessions, self.sessions = self.sessions, {}
        for session in sessions.values():
            session['timer'].cancel(); session['key'].close()
