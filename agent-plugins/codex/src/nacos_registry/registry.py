# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Adapter for the pinned Nacos 3.3 Client/Admin HTTP contracts."""
import json
import time
from urllib.parse import urlencode
import uuid

from .errors import PluginError, require
from .transport import checked_url, http, json_body, secret, error_kind


class Registry:
    def __init__(self, profile, credential_resolver=None):
        self.profile = profile
        self.tokens = {}
        self.credential_resolver = credential_resolver

    def credential(self, surface, field):
        auth = self.profile.get(surface + "Auth", {})
        if auth.get("source") == "local":
            require(self.credential_resolver is not None, "Local credential storage is unavailable", "credential_missing")
            return self.credential_resolver(self.profile, surface)[field]
        return secret(auth[field + "Env"])

    def headers(self, surface):
        config = self.profile.get(surface + "Auth", {"type": "none"})
        kind = config["type"]
        if kind == "none":
            return {}
        if kind == "token":
            return {"accessToken": self.credential(surface, "token")}
        if kind == "login":
            cached = self.tokens.get(surface)
            if not cached or cached[1] <= time.time():
                base = self.profile[surface + "Url"]
                fields = {"username": self.credential(surface, "username"), "password": self.credential(surface, "password")}
                try:
                    _, _, body = http(base + "/v3/auth/user/login", "POST", {"Content-Type": "application/x-www-form-urlencoded"}, urlencode(fields).encode())
                except PluginError as exc:
                    if exc.kind in ("authentication", "permission"):
                        raise PluginError("authentication", "Registry login credentials were rejected") from None
                    raise
                value = json_body(body)
                # Native auth login uses an unwrapped token response.
                require(isinstance(value, dict) and isinstance(value.get("accessToken"), str), "Login did not return an access token", "authentication")
                self.tokens[surface] = (value["accessToken"], time.time() + max(0, int(value.get("tokenTtl", 0)) - 30))
            return {"accessToken": self.tokens[surface][0]}
        raise PluginError("unsupported", "Unsupported registry authentication")

    def request(self, surface, route, params=None, method="GET", file=None, binary=False):
        base = checked_url(self.profile[surface + "Url"])
        headers = self.headers(surface)
        fields = {"namespaceId": self.profile["namespaceId"], **(params or {})}
        data = None
        if file is not None:
            boundary = "nacos-" + uuid.uuid4().hex
            parts = []
            for key, value in fields.items():
                parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n').encode())
            parts += [(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="skill.zip"\r\nContent-Type: application/zip\r\n\r\n').encode(), file, f'\r\n--{boundary}--\r\n'.encode()]
            data = b"".join(parts)
            headers["Content-Type"] = "multipart/form-data; boundary=" + boundary
        elif method == "GET":
            route += "?" + urlencode(fields, doseq=True)
        else:
            data = urlencode(fields, doseq=True).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        status, response_headers, body = http(base + route, method, headers, data, mutation=method != "GET" and not route.endswith("/precheck"))
        if binary:
            require(status == 304 or "zip" in response_headers.get("content-type", "").lower() or body.startswith(b"PK"), "Expected ZIP download", "protocol")
            return status, response_headers, body
        try:
            value = json_body(body)
            require(isinstance(value, dict) and "code" in value, "Invalid Nacos response envelope", "protocol")
        except PluginError:
            if method != "GET" and not route.endswith("/precheck"):
                raise PluginError("result_unknown", "Mutation response could not be verified; inspect exact server state") from None
            raise
        if value["code"] != 0:
            code = value["code"]
            kind = error_kind(200, code)
            raise PluginError(kind, "Nacos rejected the request; inspect server diagnostics", serverCode=code)
        return value.get("data")

    def search(self, query="", resourceTypes=None, cursor=None, limit=20, tagsAll=None):
        require(isinstance(query, str) and len(query) <= 1024 and isinstance(limit, int) and 1 <= limit <= 100, "Invalid search input")
        types = resourceTypes or ["skill", "mcp", "agent"]
        require(all(x in ("skill", "mcp", "agent") for x in types), "Unsupported first-release resource type")
        fields = {"query": query, "resourceTypes": types, "limit": limit}
        if cursor:
            fields["cursor"] = cursor
        if tagsAll:
            fields["tagsAll"] = tagsAll
        return self.request("client", "/v3/client/ai/resources/search", fields)

    def download(self, name, version=None, label=None):
        require(not (version and label), "Choose either version or label")
        params = {"name": name}
        if version: params["version"] = version
        if label: params["label"] = label
        _, headers, body = self.request("client", "/v3/client/ai/skills", params, binary=True)
        resolved = headers.get("x-nacos-skill-resolved-version")
        require(bool(resolved), "Server did not return a resolved Skill version", "unsupported")
        require(not version or resolved == version, "Resolved Skill version differs from requested version", "protocol")
        return resolved, headers.get("x-nacos-skill-md5"), body

    def my_skills(self, query="", page=1, limit=20):
        require(isinstance(query, str) and len(query) <= 128 and type(page) is int and page >= 1
                and type(limit) is int and 1 <= limit <= 100, "Invalid owned Skill query")
        auth = self.profile.get("adminAuth", {})
        require(auth.get("type") == "login", "Owned resources require native Admin login; token and anonymous identity cannot be verified", "unsupported")
        self.headers("admin")  # Verify the login before using its principal as an owner filter.
        owner = self.credential("admin", "username")
        result = self.request("admin", "/v3/admin/ai/skills/list", {
            "owner": owner, "skillName": query, "search": "blur", "pageNo": page, "pageSize": limit})
        require(isinstance(result, dict) and isinstance(result.get("pageItems"), list)
                and type(result.get("totalCount")) is int, "Invalid owned Skill page", "protocol")
        require(all(isinstance(item, dict) and item.get("owner") == owner for item in result["pageItems"]),
                "Server did not enforce the owner filter", "protocol")
        return {"owner": owner, "items": result["pageItems"], "page": page,
                "total": result["totalCount"], "hasMore": page * limit < result["totalCount"]}

    def skill_meta(self, name):
        result = self.request("admin", "/v3/admin/ai/skills", {"skillName": name})
        require(isinstance(result, dict) and isinstance(result.get("versions"), list), "Invalid Skill metadata", "protocol")
        return result

    def draft_zip(self, name, version):
        return self.request("admin", "/v3/admin/ai/skills/version/download", {"skillName": name, "version": version}, binary=True)[2]

    def precheck(self, data):
        return self.request("admin", "/v3/admin/ai/skills/upload/precheck", method="POST", file=data)

    def upload(self, data, action, target_version, commit_message):
        return self.request("admin", "/v3/admin/ai/skills/upload", {"uploadAction": action, "targetVersion": target_version,
                            "overwrite": str(action == "OVERWRITE_DRAFT").lower(), "autoPublishIfNew": "false", "commitMsg": commit_message}, "POST", file=data)

    def lifecycle(self, name, version, action):
        require(action in ("submit", "publish"), "Unsupported lifecycle action")
        return self.request("admin", "/v3/admin/ai/skills/" + action, {"skillName": name, "version": version}, "POST")

    def discover(self, resource_type, name, version=None):
        require(resource_type in ("mcp", "agent"), "Unsupported discovery type")
        params = {"mcpName" if resource_type == "mcp" else "agentName": name}
        if version: params["version"] = version
        if resource_type == "agent":
            params.update(protocol=["a2a"], protocolVersion="0.3.0", transport=["JSONRPC"])
        result = self.request("client", "/v3/client/ai/" + ("mcp" if resource_type == "mcp" else "agents"), params)
        require(isinstance(result, dict), "Invalid discovery response", "protocol")
        return result
