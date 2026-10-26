# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Local macOS hidden input and non-synchronizable Keychain storage."""
import ctypes as C
import json
import os
import re
import subprocess
import sys
import time

from .errors import PluginError, require
from .store import digest

FIELDS = {"login": {"username": 256, "password": 4096}, "token": {"token": 8192}}
OSASCRIPT = "/usr/bin/osascript"
DIALOG = """on run argv
	set hiddenFlag to ((item 2 of argv) is "1")
	tell me to activate
	set r to display dialog (item 1 of argv) default answer "" hidden answer hiddenFlag with title "Nacos AI Registry" buttons {"取消", "保存"} default button "保存" cancel button "取消" giving up after ((item 3 of argv) as integer) with icon note
	if gave up of r then return "T"
	return "V" & (text returned of r)
end run
"""


def reference(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{32}", value), "Invalid credential reference")
    return value


def binding(profile, surface):
    """Entry scope: plugin state root (service name), connection, identity, target, auth type and purpose."""
    return {"profileId": profile["id"], "identityId": profile["identityId"], "url": profile[surface + "Url"],
            "type": profile[surface + "Auth"]["type"],
            "purpose": "shared" if profile.get("adminMode") == "shared" else surface}


def validate_secret(kind, value):
    fields = FIELDS.get(kind)
    require(fields and isinstance(value, dict) and set(value) == set(fields), "Invalid credential fields")
    for key, limit in fields.items():
        require(isinstance(value[key], str) and 0 < len(value[key].encode("utf-8")) <= limit
                and "\x00" not in value[key], "Credential is empty or exceeds the supported size")
    return value


class Keychain:
    """macOS SecItem generic passwords scoped to the plugin state root; other platforms fail closed."""

    def __init__(self, root):
        self.service = "io.nacos.ai-registry.qoder." + digest(str(root))[:24]
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
                fn = getattr(self.cf, name)
                fn.argtypes, fn.restype = args, result
            for name in ("SecItemAdd", "SecItemCopyMatching", "SecItemDelete"):
                fn = getattr(self.sec, name)
                fn.argtypes = [C.c_void_p] if name == "SecItemDelete" else [C.c_void_p, C.POINTER(C.c_void_p)]
                fn.restype = C.c_int32
            self.available = True
        except (OSError, AttributeError):
            pass

    def capabilities(self):
        return {"available": self.available, "backend": "macos-keychain" if self.available else None,
                "reason": None if self.available else "secure_store_unavailable"}

    def _constant(self, name):
        return C.c_void_p.in_dll(self.cf if name.startswith("kCF") else self.sec, name).value

    def _query(self, ref, action, payload=None):
        require(self.available, "System Keychain is unavailable; use environment references or configure later", "secure_store_unavailable")
        reference(ref)
        owned, result = [], C.c_void_p()

        def string(value):
            pointer = self.cf.CFStringCreateWithCString(None, value.encode(), 0x08000100)
            require(pointer, "Keychain allocation failed", "credential_store")
            owned.append(pointer)
            return pointer

        query = self.cf.CFDictionaryCreateMutable(None, 0, None, None)
        require(query, "Keychain allocation failed", "credential_store")
        owned.append(query)
        try:
            fields = {"kSecClass": self._constant("kSecClassGenericPassword"),
                      "kSecAttrService": string(self.service), "kSecAttrAccount": string(ref),
                      "kSecAttrSynchronizable": self._constant("kCFBooleanFalse")}
            if action == "put":
                raw = json.dumps(payload, ensure_ascii=False).encode()
                data = self.cf.CFDataCreate(None, raw, len(raw))
                require(data, "Keychain allocation failed", "credential_store")
                owned.append(data)
                fields["kSecValueData"] = data
                fields["kSecAttrLabel"] = string("Nacos AI Registry (Qoder)")
            elif action == "get":
                fields["kSecReturnData"] = self._constant("kCFBooleanTrue")
                fields["kSecMatchLimit"] = self._constant("kSecMatchLimitOne")
            for key, value in fields.items():
                self.cf.CFDictionarySetValue(query, self._constant(key), value)
            if action == "delete":
                code = self.sec.SecItemDelete(query)
            else:
                code = (self.sec.SecItemAdd if action == "put" else self.sec.SecItemCopyMatching)(query, C.byref(result))
            if code == -25300:
                if action == "delete":
                    return None
                raise PluginError("credential_missing", "Saved credential is missing from Keychain; enter it again")
            require(code == 0, "Keychain denied the operation; allow access and retry", "credential_store")
            if action == "get":
                length = self.cf.CFDataGetLength(result)
                require(0 < length <= 32768, "Invalid saved credential", "credential_store")
                try:
                    return json.loads(C.string_at(self.cf.CFDataGetBytePtr(result), length))
                except (ValueError, UnicodeError):
                    raise PluginError("credential_store", "Invalid saved credential") from None
            return None
        finally:
            if result.value:
                self.cf.CFRelease(result)
            for pointer in reversed(owned):
                self.cf.CFRelease(pointer)

    def put(self, ref, payload):
        self._query(ref, "put", payload)

    def get(self, ref):
        return self._query(ref, "get")

    def delete(self, ref):
        self._query(ref, "delete")


class NativePrompt:
    """Local macOS dialog shown by the plugin process; typed values return only to this process."""

    def __init__(self, wait=120, budget=240):
        self.wait, self.budget = wait, budget

    def capabilities(self):
        available = sys.platform == "darwin" and os.access(OSASCRIPT, os.X_OK)
        return {"available": available, "backend": "macos-dialog" if available else None,
                "reason": None if available else "secure_input_unavailable"}

    def ask(self, text, hidden, wait):
        try:
            completed = subprocess.run([OSASCRIPT, "-", text, "1" if hidden else "0", str(wait)],
                                       input=DIALOG.encode(), capture_output=True, timeout=wait + 30,
                                       env={"PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8"})
        except subprocess.TimeoutExpired:
            raise PluginError("timed_out", "Credential dialog timed out; nothing was saved") from None
        except OSError:
            raise PluginError("secure_input_unavailable", "Native credential dialog is unavailable") from None
        if completed.returncode != 0:
            if b"-128" in completed.stderr:
                raise PluginError("cancelled", "Credential entry was cancelled; nothing was saved")
            raise PluginError("secure_input_unavailable", "Native credential dialog could not be shown")
        output = completed.stdout.decode("utf-8", "strict")
        if output.endswith("\n"):
            output = output[:-1]
        if output == "T":
            raise PluginError("timed_out", "Credential dialog timed out; nothing was saved")
        require(output.startswith("V"), "Unexpected credential dialog result", "secure_input_unavailable")
        return output[1:]

    def collect(self, kind, label, url):
        require(self.capabilities()["available"], "Native credential dialog requires local macOS", "secure_input_unavailable")
        deadline = time.monotonic() + self.budget
        prompts = {"login": [("username", False, "用户名"), ("password", True, "密码")],
                   "token": [("token", True, "Access Token")]}[kind]
        value = {}
        for field, hidden, name in prompts:
            wait = int(min(self.wait, deadline - time.monotonic()))
            require(wait >= 5, "Credential entry exceeded the time limit; nothing was saved", "timed_out")
            text = f"Nacos AI Registry 请求保存 {label} {name}\n目标：{url}\n\n输入仅保存到本机钥匙串，不会发送到对话。"
            value[field] = self.ask(text, hidden, wait)
            require(value[field], "Credential is empty; nothing was saved", "empty")
        return validate_secret(kind, value)
