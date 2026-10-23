# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Local credentials. No shell, environment mutation, plaintext file or cloud sync."""
import ctypes as C
import json
import re
import sys

from .errors import PluginError, require
from .store import digest


def reference(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{32}", value), "Invalid credential reference")
    return value


def binding(profile, surface):
    return {"profileId": profile["id"], "identityId": profile["identityId"],
            "url": profile[surface + "Url"], "type": profile[surface + "Auth"]["type"]}


def validate_secret(kind, value):
    fields = {"login": {"username": 256, "password": 4096}, "token": {"token": 8192}}.get(kind)
    require(fields and isinstance(value, dict) and set(value) == set(fields), "Invalid credential fields")
    for key, limit in fields.items():
        require(isinstance(value[key], str) and 0 < len(value[key].encode("utf-8")) <= limit
                and "\x00" not in value[key], "Credential is empty or exceeds the supported size")
    return value


class SecurityFramework:
    """Shared native bindings; constructing this object does not access credentials."""
    def __init__(self):
        self.available = False
        if sys.platform != "darwin":
            return
        try:
            self.cf = C.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
            self.sec = C.CDLL("/System/Library/Frameworks/Security.framework/Security")
            for name, args, result in [
                ("CFStringCreateWithCString", [C.c_void_p, C.c_char_p, C.c_uint32], C.c_void_p),
                ("CFDataCreate", [C.c_void_p, C.c_char_p, C.c_long], C.c_void_p),
                ("CFDataGetLength", [C.c_void_p], C.c_long),
                ("CFDataGetBytePtr", [C.c_void_p], C.c_void_p),
                ("CFDictionaryCreateMutable", [C.c_void_p, C.c_long, C.c_void_p, C.c_void_p], C.c_void_p),
                ("CFDictionarySetValue", [C.c_void_p, C.c_void_p, C.c_void_p], None),
                ("CFRelease", [C.c_void_p], None),
            ]:
                fn = getattr(self.cf, name); fn.argtypes = args; fn.restype = result
            for name in ("SecItemAdd", "SecItemCopyMatching", "SecItemDelete"):
                fn = getattr(self.sec, name)
                fn.argtypes = [C.c_void_p] if name == "SecItemDelete" else [C.c_void_p, C.POINTER(C.c_void_p)]
                fn.restype = C.c_int32
            self.available = True
        except (OSError, AttributeError):
            pass

    def _constant(self, name):
        return C.c_void_p.in_dll(self.cf if name.startswith("kCF") else self.sec, name).value


class Keychain(SecurityFramework):
    """Non-synchronizable SecItem passwords scoped to the plugin state directory.

    Python is the accessing executable; macOS may request Keychain permission.
    Other platforms fail closed.
    """
    def __init__(self, root):
        super().__init__()
        self.service = "io.nacos.ai-registry." + digest(str(root))[:24]

    def capabilities(self):
        return {"available": self.available, "backend": "macos-keychain" if self.available else None,
                "reason": None if self.available else "secure_store_unavailable"}

    def _query(self, ref, action, payload=None):
        require(self.available, "System credential storage is unavailable; choose environment references", "secure_store_unavailable")
        reference(ref)
        owned = []
        def string(value):
            ptr = self.cf.CFStringCreateWithCString(None, value.encode(), 0x08000100)
            require(ptr, "Credential storage allocation failed", "credential_store")
            owned.append(ptr); return ptr
        query = self.cf.CFDictionaryCreateMutable(None, 0, None, None)
        require(query, "Credential storage allocation failed", "credential_store")
        owned.append(query)
        result = C.c_void_p()
        try:
            fields = {"kSecClass": self._constant("kSecClassGenericPassword"),
                      "kSecAttrService": string(self.service), "kSecAttrAccount": string(ref),
                      "kSecAttrSynchronizable": self._constant("kCFBooleanFalse")}
            if action == "put":
                raw = json.dumps(payload, ensure_ascii=False).encode()
                ptr = self.cf.CFDataCreate(None, raw, len(raw))
                require(ptr, "Credential storage allocation failed", "credential_store")
                owned.append(ptr); fields["kSecValueData"] = ptr
                fields["kSecAttrLabel"] = string("Nacos AI Registry")
            if action == "get":
                fields.update(kSecReturnData=self._constant("kCFBooleanTrue"),
                              kSecMatchLimit=self._constant("kSecMatchLimitOne"))
            for key, value in fields.items():
                self.cf.CFDictionarySetValue(query, self._constant(key), value)
            fn = {"put": self.sec.SecItemAdd, "get": self.sec.SecItemCopyMatching, "delete": self.sec.SecItemDelete}[action]
            code = fn(query) if action == "delete" else fn(query, C.byref(result))
            if code == -25300 and action == "delete": return
            if code == -25300: raise PluginError("credential_missing", "Saved credentials are missing; enter them again in Settings")
            require(code == 0, "System credential storage denied the operation; check Keychain access and retry", "credential_store")
            if action == "get":
                length = self.cf.CFDataGetLength(result)
                require(0 < length <= 32768, "Invalid saved credential", "credential_store")
                try: return json.loads(C.string_at(self.cf.CFDataGetBytePtr(result), length))
                except (ValueError, UnicodeError): raise PluginError("credential_store", "Invalid saved credential") from None
        finally:
            if result.value: self.cf.CFRelease(result)
            for ptr in reversed(owned): self.cf.CFRelease(ptr)

    def put(self, ref, payload): self._query(ref, "put", payload)
    def get(self, ref): return self._query(ref, "get")
    def delete(self, ref): self._query(ref, "delete")
