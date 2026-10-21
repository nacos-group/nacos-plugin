# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Pinned discovery snapshots and separately authenticated downstream clients."""
import json
import re
import uuid
from urllib.parse import urlsplit

from . import __version__
from .errors import require, PluginError
from .transport import checked_url, http, json_body, secret


def auth_config(value):
    value = value or {"type": "none"}
    require(value.get("type") in ("none", "bearer"), "Only explicit none/bearer downstream authentication is implemented")
    require(set(value) == ({"type"} if value["type"] == "none" else {"type", "tokenEnv"}), "Downstream credentials must use environment references")
    if value["type"] == "bearer":
        require(re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", value["tokenEnv"]) is not None, "Invalid credential reference")
    return value


def auth_headers(auth):
    return {"Authorization": "Bearer " + secret(auth["tokenEnv"])} if auth["type"] == "bearer" else {}


def endpoints(kind, detail):
    choices = []
    if kind == "mcp":
        require(detail.get("enabled", True) and detail.get("status", "active").lower() not in ("inactive", "disabled"), "MCP service is disabled", "unavailable")
        require(detail.get("frontProtocol") in ("mcp-streamable", "streamable-http") or detail.get("protocol") in ("mcp-streamable", "streamable-http"), "MCP transport is unsupported", "unsupported")
        declared = detail.get("frontendEndpoints") or []
        if not declared and detail.get("protocol") in ("mcp-streamable", "streamable-http"):
            # Native MCP services use backendEndpoints in Nacos. A plain HTTP backend
            # still needs a separately declared MCP frontend; never treat it as MCP.
            declared = detail.get("backendEndpoints") or []
        for endpoint in declared:
            scheme = endpoint.get("protocol")
            require(scheme in ("http", "https"), "MCP frontend transport requires an HTTP(S) URL", "unsupported")
            address, port, path = endpoint.get("address"), endpoint.get("port"), endpoint.get("path") or ""
            require(isinstance(address, str) and address and not any(c in address for c in "/@?#"), "Invalid endpoint address")
            require(isinstance(port, int) and 1 <= port <= 65535 and (not path or path.startswith("/")), "Invalid endpoint port/path")
            if ":" in address and not address.startswith("["): address = "[" + address + "]"
            url = checked_url(f"{scheme}://{address}:{port}{path}")
            choices.append({"url": url, "transport": "streamable-http"})
    else:
        for interface in detail.get("callInterfaces") or []:
            if interface.get("protocol", "").lower() != "a2a" or interface.get("protocolVersion") != "0.3.0":
                continue
            descriptor = interface.get("nativeDescriptor")
            require(isinstance(descriptor, dict) and descriptor.get("protocolVersion") == "0.3.0", "A2A descriptor does not confirm 0.3.0", "unsupported")
            require(descriptor.get("preferredTransport", "JSONRPC") == "JSONRPC", "Only A2A JSONRPC supported", "unsupported")
            sets = interface.get("endpointSets") or []
            order = interface.get("endpointSourceOrder") or []
            sets = sorted(sets, key=lambda x: order.index(x.get("source")) if x.get("source") in order else len(order))
            for group in sets:
                valid = [e for e in group.get("endpoints", []) if e.get("healthy", True) and e.get("enabled", True) and e.get("transport") == "JSONRPC"]
                if valid:
                    for e in sorted(valid, key=lambda x: x.get("priority", 0)):
                        choices.append({"url": checked_url(e["uri"]), "transport": "JSONRPC", "protocolVersion": "0.3.0", "source": group.get("source")})
                    break
    require(bool(choices), "No supported and available frontend endpoint", "unavailable")
    return choices


class JsonRpc:
    def __init__(self, url, auth, protocol=None):
        self.url, self.auth = checked_url(url), auth_config(auth)
        self.protocol, self.session = protocol, None

    def request(self, method, params, notification=False, mutation=False):
        identifier = uuid.uuid4().hex
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        if not notification: payload["id"] = identifier
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **auth_headers(self.auth)}
        if self.protocol: headers["MCP-Protocol-Version"] = self.protocol
        if self.session: headers["Mcp-Session-Id"] = self.session
        status, response_headers, body = http(self.url, "POST", headers, json.dumps(payload).encode(), mutation=mutation)
        if response_headers.get("mcp-session-id"):
            self.session = response_headers["mcp-session-id"]
        if notification:
            require(status in (200, 202, 204), "Notification rejected", "protocol")
            return None
        if "text/event-stream" in response_headers.get("content-type", ""):
            # Finite event responses only. Streaming tasks are outside this release.
            responses = []
            try:
                for event in body.decode().replace("\r\n", "\n").split("\n\n"):
                    parts = [x[5:].lstrip() for x in event.splitlines() if x.startswith("data:")]
                    if parts:
                        value = json_body("\n".join(parts))
                        if isinstance(value, dict) and value.get("id") == identifier: responses.append(value)
            except (PluginError, UnicodeError):
                raise PluginError("result_unknown" if mutation else "protocol", "Downstream event response could not be verified") from None
            require(len(responses) == 1, "Stream did not yield exactly one matching RPC response", "result_unknown" if mutation else "protocol")
            value = responses[0]
        else:
            try:
                value = json_body(body)
            except PluginError:
                if mutation:
                    raise PluginError("result_unknown", "Downstream write response is unverified") from None
                raise
        require(isinstance(value, dict) and value.get("jsonrpc") == "2.0" and value.get("id") == identifier, "RPC response identity mismatch", "result_unknown" if mutation else "protocol")
        if "error" in value:
            require(isinstance(value["error"], dict), "Invalid RPC error", "result_unknown" if mutation else "protocol")
            raise PluginError("downstream", "Downstream RPC rejected the request; content omitted", rpcCode=value["error"].get("code"))
        require("result" in value, "RPC response has no result", "result_unknown" if mutation else "protocol")
        return value["result"]

    def initialize_mcp(self):
        result = self.request("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "nacos-ai-registry", "version": __version__}})
        require(isinstance(result, dict), "Invalid initialize response", "protocol")
        require(result.get("protocolVersion") in ("2024-11-05", "2025-03-26", "2025-06-18"), "Unsupported MCP protocol version", "unsupported")
        self.protocol = result["protocolVersion"]
        self.request("notifications/initialized", {}, notification=True)
        return result

    def close_mcp(self):
        if self.session:
            try:
                http(self.url, "DELETE", {**auth_headers(self.auth), "Mcp-Session-Id": self.session, "MCP-Protocol-Version": self.protocol})
            except PluginError:
                pass  # Session deletion is best effort; never affects business-operation status.
