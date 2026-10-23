# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""JWE RSA-OAEP-256 / A256CBC-HS512 using native RSA/AES and stdlib HMAC.

RFC 7516 compact serialization; RFC 7518 sections 4.3 and 5.2.5.
Private RSA keys are ephemeral SecKey objects, never exported or persisted.
"""
import base64
import ctypes as C
import hashlib
import hmac
import json
import re

from .credentials import SecurityFramework
from .errors import PluginError, require


def b64(data): return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def unb64(value, maximum):
    require(isinstance(value, str) and 0 < len(value) <= maximum and re.fullmatch(r"[A-Za-z0-9_-]+", value),
            "Invalid encrypted credential request", "credential_envelope")
    try: result = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except ValueError: raise PluginError("credential_envelope", "Invalid encrypted credential request") from None
    require(b64(result) == value, "Invalid encrypted credential request", "credential_envelope")
    return result


def parse(envelope):
    require(isinstance(envelope, str) and len(envelope) <= 46000, "Invalid encrypted credential request", "credential_envelope")
    parts = envelope.split(".")
    require(len(parts) == 5, "Invalid encrypted credential request", "credential_envelope")
    try: header = json.loads(unb64(parts[0], 512))
    except (ValueError, UnicodeError): raise PluginError("credential_envelope", "Invalid encrypted credential request") from None
    require(isinstance(header, dict) and set(header) == {"alg", "enc", "kid"}
            and header["alg"] == "RSA-OAEP-256" and header["enc"] == "A256CBC-HS512"
            and isinstance(header["kid"], str) and re.fullmatch(r"[A-Za-z0-9_-]{43}", header["kid"]),
            "Unsupported encrypted credential request", "credential_envelope")
    wrapped, iv, ciphertext, tag = [unb64(p, limit) for p, limit in zip(parts[1:], (344, 24, 44000, 44))]
    require(len(wrapped) == 256 and len(iv) == 16 and 0 < len(ciphertext) <= 32784
            and len(ciphertext) % 16 == 0 and len(tag) == 32,
            "Invalid encrypted credential request", "credential_envelope")
    return header, parts[0].encode("ascii"), wrapped, iv, ciphertext, tag


def authenticate(cek, aad, iv, ciphertext, tag):
    require(len(cek) == 64, "Invalid encrypted credential request", "credential_envelope")
    length = (len(aad) * 8).to_bytes(8, "big")
    expected = hmac.new(cek[:32], aad + iv + ciphertext + length, hashlib.sha512).digest()[:32]
    require(hmac.compare_digest(expected, tag), "Invalid encrypted credential request", "credential_envelope")


def der(tag, value):
    length = len(value)
    size = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([tag]) + (bytes([length]) if length < 128 else bytes([128 + len(size)]) + size) + value


class EphemeralKey:
    def __init__(self):
        self.api = SecurityFramework(); self.key = None
        require(self.api.available, "Local credential encryption is unavailable", "secure_store_unavailable")
        cf, sec = self.api.cf, self.api.sec
        cf.CFNumberCreate.argtypes = [C.c_void_p, C.c_int, C.c_void_p]; cf.CFNumberCreate.restype = C.c_void_p
        for name, args in [
            ("SecKeyCreateRandomKey", [C.c_void_p, C.POINTER(C.c_void_p)]),
            ("SecKeyCopyPublicKey", [C.c_void_p]),
            ("SecKeyCopyExternalRepresentation", [C.c_void_p, C.POINTER(C.c_void_p)]),
            ("SecKeyCreateDecryptedData", [C.c_void_p, C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p)]),
        ]:
            fn = getattr(sec, name); fn.argtypes = args; fn.restype = C.c_void_p
        self.cc = C.CDLL('/usr/lib/system/libcommonCrypto.dylib')
        self.cc.CCCrypt.argtypes = [C.c_uint32, C.c_uint32, C.c_uint32, C.c_void_p, C.c_size_t,
                                   C.c_void_p, C.c_void_p, C.c_size_t, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
        self.cc.CCCrypt.restype = C.c_int32
        bits = C.c_int32(2048)
        number = cf.CFNumberCreate(None, 3, C.byref(bits))  # kCFNumberSInt32Type
        params = cf.CFDictionaryCreateMutable(None, 0, None, None)
        error = C.c_void_p()
        try:
            require(number and params, "Local credential encryption is unavailable", "credential_channel")
            cf.CFDictionarySetValue(params, self.api._constant('kSecAttrKeyType'), self.api._constant('kSecAttrKeyTypeRSA'))
            cf.CFDictionarySetValue(params, self.api._constant('kSecAttrKeySizeInBits'), number)
            self.key = sec.SecKeyCreateRandomKey(params, C.byref(error))
            require(self.key, "Local credential encryption is unavailable", "credential_channel")
        finally:
            for ptr in (params, number, error.value):
                if ptr: cf.CFRelease(ptr)

    def data(self, ptr, maximum):
        require(ptr, "Invalid encrypted credential request", "credential_envelope")
        size = self.api.cf.CFDataGetLength(ptr)
        require(0 < size <= maximum, "Invalid encrypted credential request", "credential_envelope")
        return C.string_at(self.api.cf.CFDataGetBytePtr(ptr), size)

    def public_key(self):
        public = raw = None; error = C.c_void_p()
        try:
            public = self.api.sec.SecKeyCopyPublicKey(self.key)
            require(public, "Local credential encryption is unavailable", "credential_channel")
            raw = self.api.sec.SecKeyCopyExternalRepresentation(public, C.byref(error))
            # SecKey exports PKCS#1. Wrap rsaEncryption AlgorithmIdentifier + BIT STRING in SPKI.
            pkcs1 = self.data(raw, 1024)
            return b64(der(0x30, bytes.fromhex('300d06092a864886f70d0101010500') + der(0x03, b'\0' + pkcs1)))
        finally:
            for ptr in (raw, public, error.value):
                if ptr: self.api.cf.CFRelease(ptr)

    def unwrap(self, wrapped):
        value = self.api.cf.CFDataCreate(None, wrapped, len(wrapped)); result = None; error = C.c_void_p()
        try:
            require(value, "Invalid encrypted credential request", "credential_envelope")
            result = self.api.sec.SecKeyCreateDecryptedData(self.key,
                self.api._constant('kSecKeyAlgorithmRSAEncryptionOAEPSHA256'), value, C.byref(error))
            return self.data(result, 64)
        finally:
            for ptr in (result, value, error.value):
                if ptr: self.api.cf.CFRelease(ptr)

    def decrypt(self, parsed):
        _, aad, wrapped, iv, ciphertext, tag = parsed
        cek = self.unwrap(wrapped)
        # Authenticate before CBC decryption; no padding oracle or unauthenticated plaintext.
        authenticate(cek, aad, iv, ciphertext, tag)
        output = C.create_string_buffer(len(ciphertext) + 16); written = C.c_size_t()
        code = self.cc.CCCrypt(1, 0, 1, cek[32:], 32, iv, ciphertext, len(ciphertext),
                               output, len(output), C.byref(written))  # decrypt, AES, PKCS7
        try:
            require(code == 0 and written.value <= 32768, "Invalid encrypted credential request", "credential_envelope")
            return json.loads(output.raw[:written.value])
        except (ValueError, UnicodeError): raise PluginError("credential_envelope", "Invalid encrypted credential request") from None
        finally: C.memset(output, 0, len(output))

    def close(self):
        if self.key: self.api.cf.CFRelease(self.key); self.key = None
