# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Bounded client for an already-running Codex App Server control socket.

Never starts an app-server, resumes a thread, sends a turn, or approves requests.
No reachable control socket is a supported fallback, including stdio-only desktops.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import struct
import time
import uuid

from ..errors import PluginError, require

MAX_FRAME = 2 * 1024 * 1024


class ControlClient:
    """RFC 6455 text frames over the documented local Unix socket transport."""
    def __init__(self, socket_path):
        require(hasattr(socket, "AF_UNIX"), "Native Unix control transport unavailable", "native_unavailable")
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.identifier = 0
        self.deadline = time.monotonic() + 3
        try:
            self.socket.settimeout(3)
            self.socket.connect(socket_path)
            key = base64.b64encode(os.urandom(16)).decode()
            request = ("GET / HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\n"
                       "Connection: Upgrade\r\nSec-WebSocket-Version: 13\r\n"
                       "Sec-WebSocket-Key: " + key + "\r\n\r\n")
            self.socket.sendall(request.encode())
            header = bytearray()
            while not header.endswith(b"\r\n\r\n"):
                require(len(header) < 8192, "Invalid native websocket handshake", "native_unavailable")
                header.extend(self._exact(1))
            lines = header.decode("ascii").split("\r\n")
            headers = dict(line.split(":", 1) for line in lines[1:] if ":" in line)
            headers = {k.lower(): v.strip().lower() if k.lower() in ("upgrade", "connection") else v.strip() for k, v in headers.items()}
            expected = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            require(len(lines[0].split()) >= 2 and lines[0].split()[1] == "101" and headers.get("upgrade") == "websocket"
                    and "upgrade" in headers.get("connection", "").split(", ")
                    and headers.get("sec-websocket-accept") == expected,
                    "Native websocket handshake rejected", "native_unavailable")
        except Exception:
            self.socket.close()
            raise

    def _exact(self, count):
        result = bytearray()
        while len(result) < count:
            remaining = self.deadline - time.monotonic()
            require(remaining > 0, "Native response timed out", "native_timeout")
            self.socket.settimeout(remaining)
            chunk = self.socket.recv(count - len(result))
            require(bool(chunk), "Native control connection closed", "native_unavailable")
            result.extend(chunk)
        return bytes(result)

    def _frame(self, opcode, payload):
        require(len(payload) <= MAX_FRAME, "Native frame exceeds limit", "native_unavailable")
        mask = os.urandom(4)
        size = len(payload)
        length = bytes([0x80 | size]) if size < 126 else bytes([0x80 | 126]) + struct.pack("!H", size) if size < 65536 else bytes([0x80 | 127]) + struct.pack("!Q", size)
        self.socket.sendall(bytes([0x80 | opcode]) + length + mask + bytes(x ^ mask[i % 4] for i, x in enumerate(payload)))

    def send(self, message):
        self._frame(1, json.dumps(message, allow_nan=False).encode())

    def _message(self, deadline):
        data, started = bytearray(), False
        while True:
            require(time.monotonic() < deadline, "Native response timed out", "native_timeout")
            self.socket.settimeout(max(.001, deadline - time.monotonic()))
            first, second = self._exact(2)
            opcode, final = first & 15, bool(first & 128)
            require(not first & 112 and not second & 128, "Invalid native websocket frame", "native_unavailable")
            size = second & 127
            if size == 126: size = struct.unpack("!H", self._exact(2))[0]
            elif size == 127: size = struct.unpack("!Q", self._exact(8))[0]
            require(size <= MAX_FRAME - len(data), "Native response exceeds limit", "native_unavailable")
            if opcode >= 8:
                require(final and size <= 125, "Invalid websocket control frame", "native_unavailable")
            payload = self._exact(size)
            if opcode == 8: raise PluginError("native_unavailable", "Native websocket closed")
            if opcode == 9:
                self._frame(10, payload); continue
            if opcode == 10: continue
            require(opcode == (0 if started else 1), "Expected native text response", "native_unavailable")
            data.extend(payload); started = True
            if final:
                value = json.loads(data)
                require(isinstance(value, dict), "Invalid native response", "native_unavailable")
                return value

    def request(self, method, params=None, timeout=8):
        self.identifier += 1
        identifier = self.identifier
        deadline = time.monotonic() + timeout
        self.deadline = deadline
        self.send({"id": identifier, "method": method, "params": params})
        while True:
            message = self._message(deadline)
            if "method" in message and "id" in message:
                # Never turn the plugin into an approval or callback bypass.
                self.send({"id": message["id"], "error": {"code": -32601, "message": "Unsupported client request"}})
            elif message.get("id") == identifier:
                require("error" not in message, "Native control request was rejected", "native_rejected")
                require("result" in message, "Invalid native control response", "native_unavailable")
                return message["result"]

    def close(self):
        self.socket.close()


def control_socket(config_path):
    home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser()
    require(home.is_absolute(), "CODEX_HOME must be absolute", "native_unavailable")
    require(Path(config_path).resolve() == (home / "config.toml").resolve(),
            "Native refresh requires this Codex host's user configuration", "native_config_mismatch")
    socket_path = Path(os.environ.get("NACOS_PLUGIN_CODEX_CONTROL_SOCKET") or home / "app-server-control/app-server-control.sock")
    require(socket_path.is_absolute(), "Invalid native control socket", "native_unavailable")
    try:
        # Codex may publish a symlink to a shorter private socket path to fit
        # macOS sockaddr_un limits. Both link and target must be user-owned.
        require(hasattr(os, "getuid") and socket_path.lstat().st_uid == os.getuid(),
                "Native socket locator must belong to the current user", "native_unavailable")
        socket_path = socket_path.resolve(strict=True)
        info = socket_path.stat()
    except OSError:
        raise PluginError("native_unavailable", "This Codex instance exposes no control socket; use Settings > MCP servers > Restart") from None
    require(stat.S_ISSOCK(info.st_mode) and hasattr(os, "getuid") and info.st_uid == os.getuid(),
            "Native control socket must belong to the current local user", "native_unavailable")
    return str(socket_path)


def refresh(server, thread_id, config_path):
    base = {"threadId": thread_id, "hostLoaded": "unverified", "realUse": "unverified",
            "currentTurnTools": "unverified"}
    client, requested = None, False
    try:
        require(isinstance(thread_id, str) and str(uuid.UUID(thread_id)) == thread_id,
                "Use the current conversation's exact thread ID")
        client = ControlClient(control_socket(config_path))
        client.request("initialize", {"clientInfo": {"name": "nacos-native-refresh", "version": "1"},
                                      "capabilities": {"experimentalApi": True}})
        client.send({"method": "initialized"})
        cursor, found = None, False
        for _ in range(10):
            page = client.request("thread/loaded/list", {"limit": 100, "cursor": cursor})
            require(isinstance(page, dict), "Invalid loaded thread response", "native_unavailable")
            if thread_id in page.get("data", []):
                found = True; break
            cursor = page.get("nextCursor")
            if not cursor: break
        require(found, "Current conversation is not loaded in this App Server; no refresh was sent", "native_thread_mismatch")
        requested = True
        client.request("config/mcpServer/reload")
        status = client.request("mcpServerStatus/list", {"threadId": thread_id, "serverName": server,
                                                       "detail": "toolsAndAuthOnly"}, timeout=12)
        require(isinstance(status, dict), "Invalid native MCP status", "native_unavailable")
        match = next((x for x in status.get("data", []) if isinstance(x, dict) and x.get("name") == server), None)
        names = sorted(match.get("tools", {})) if match else []
        available = bool(names and match.get("runtimeStatus") == "connected" and not match.get("toolsError"))
        return {**base, "refresh": "queued", "hostLoaded": "available" if available else "pending",
                "tools": names, "nextStep": "Recheck the current conversation tool catalog; call the named native tool only if exposed. A queued refresh does not prove this turn has adopted it."}
    except (PluginError, OSError, ValueError) as exc:
        kind = exc.kind if isinstance(exc, PluginError) else "native_unavailable"
        return {**base, "refresh": "unverified" if requested else "unavailable", "reason": kind,
                "detail": str(exc) if isinstance(exc, PluginError) else "Native transport could not be verified",
                "nextStep": "Use Codex Settings > MCP servers > Restart and recheck this conversation. Continue an authorized trial route if useful; do not reinstall or claim native loading."}
    finally:
        if client: client.close()
