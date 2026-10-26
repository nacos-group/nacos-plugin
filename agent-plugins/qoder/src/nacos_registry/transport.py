# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""HTTP transport: explicit origins, bounded responses, no redirects or retries."""
import json
import os
import re
import socket
from http.client import HTTPException
from urllib import request, error, parse

from .errors import PluginError, require
from .package import MAX_BYTES


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def checked_url(url):
    require(isinstance(url, str), "URL must be a string")
    p = parse.urlsplit(url)
    require(p.scheme in ("http", "https") and p.hostname and not p.username and not p.password and not p.fragment and not p.query,
            "URL requires http(s), host, and no embedded credentials/query/fragment")
    require(not any(ord(c) < 33 for c in url), "Invalid URL characters")
    # Parse port now rather than allowing failures after mutation begins.
    try:
        p.port
    except ValueError:
        raise PluginError("validation", "Invalid URL port") from None
    return url.rstrip("/")


def secret(ref):
    require(isinstance(ref, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", ref), "Credential must reference an environment variable")
    value = os.environ.get(ref)
    require(bool(value), "Required credential environment variable is not set", "authentication")
    return value


def error_kind(status, code=None, mutation=False):
    if status == 401: return "authentication"
    if status == 403: return "permission"
    if mutation and status >= 500: return "result_unknown"
    codes = {10000: "validation", 10001: "permission", 20001: "validation", 20002: "validation", 20003: "validation",
             20004: "not_found", 20005: "conflict", 40001: "unsupported", 50000: "not_found", 50001: "not_found",
             50002: "conflict", 50003: "unavailable", 50100: "not_found", 50101: "not_found", 50102: "conflict", 50105: "temporarily_unavailable"}
    return codes.get(code, {404: "not_found", 409: "conflict", 405: "unsupported", 400: "validation"}.get(status, "http"))


def http(url, method="GET", headers=None, data=None, timeout=20, mutation=False):
    req = request.Request(url, data=data, headers=headers or {}, method=method)
    opener = request.build_opener(NoRedirect())
    try:
        with opener.open(req, timeout=timeout) as response:
            body = response.read(MAX_BYTES + 1)
            require(len(body) <= MAX_BYTES, "Response exceeds limit", "result_unknown" if mutation else "protocol")
            return response.status, dict((k.lower(), v) for k, v in response.headers.items()), body
    except error.HTTPError as exc:
        if exc.code == 304:
            return 304, dict((k.lower(), v) for k, v in exc.headers.items()), b""
        code = None
        try:
            value = json.loads(exc.read(65536))
            if isinstance(value, dict) and isinstance(value.get("code"), int): code = value["code"]
        except (ValueError, OSError, UnicodeError):
            pass
        kind = error_kind(exc.code, code, mutation)
        raise PluginError(kind, "HTTP request rejected; response content omitted", httpStatus=exc.code, serverCode=code) from None
    except (error.URLError, TimeoutError, socket.timeout, ConnectionError, OSError, HTTPException):
        raise PluginError("result_unknown" if mutation else "connection", "Request did not complete; do not blindly retry writes") from None


def json_body(body):
    try:
        return json.loads(body)
    except (ValueError, UnicodeDecodeError):
        raise PluginError("protocol", "Expected a JSON response") from None
