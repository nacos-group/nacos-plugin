# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Intent-based discovery: local reuse preference and install-free trials.

Discovery results are data. Saving, loading and real use are separate facts and
each needs its own evidence.
"""
import os
import time

from . import package
from .downstream import JsonRpc, auth_config
from .errors import PluginError, require
from .store import digest

INSTALL_POLICIES = ("ask", "auto", "never")
SEARCH_BUDGET = {"requests": 3, "itemsPerRequest": 20, "paginationCounts": True}
REUSE_ASK = ("Call the Qoder native question tool AskUserQuestion; fall back to chat text only when it is not "
             "exposed or reports itself unavailable. No answer, a closed dialog or a timeout is not consent.")
PREVIEW_BYTES = 256 * 1024
TRIAL_TOOL_PAGES = 5
TRIAL_TOOL_LIMIT = 500
TRIAL_TEXT_LIMIT = 65536


class DiscoveryMixin:
    def discovery_settings(self):
        stored = (self.data.get("discovery") or {}).get("installPolicy", "ask")
        require(stored in INSTALL_POLICIES, "Stored discovery preference is unknown; save it again", "configuration")
        return {"installPolicy": stored, "scope": "implicit_discovery",
                "installTiming": "after_successful_use", "explicitRequests": "independent",
                "selfChange": "not_permitted", "askInterface": REUSE_ASK, "searchBudget": dict(SEARCH_BUDGET)}

    def reuse_decision(self):
        """Carried by trial results so the rule is present where the decision is made."""
        policy = self.discovery_settings()["installPolicy"]
        decision = {"installPolicy": policy, "timing": "after_successful_use"}
        if policy == "ask":
            decision["askInterface"] = REUSE_ASK
        return decision

    def configure_discovery(self, installPolicy):
        require(installPolicy in INSTALL_POLICIES, "Choose ask, auto or never")
        self.data["discovery"] = {"installPolicy": installPolicy, "updatedAt": time.time()}
        self.store.save()
        return self.discovery_settings()

    def check_discovery_reuse(self, mode):
        """Enforced when the plan is created and again before it is applied."""
        if mode is None:
            return None
        require(mode in ("automatic", "confirmed"), "Discovery provenance must be automatic or confirmed")
        policy = self.discovery_settings()["installPolicy"]
        require(policy != "never", "Local preference never: implicitly discovered resources are not saved", "permission")
        require(mode != "automatic" or policy == "auto",
                "Automatic reuse requires the auto preference; ask the user instead", "permission")
        return mode

    def separate_downstream(self, auth):
        if auth["type"] != "bearer":
            return auth
        refs = [value for field in ("clientAuth", "adminAuth")
                for key, value in self.profile()[field].items() if key.endswith("Env")]
        require(auth["tokenEnv"] not in refs, "Use a separate downstream credential reference")
        token = os.environ.get(auth["tokenEnv"])
        require(not token or token not in self.nacos_secret_values(), "Use a separate downstream credential value")
        return auth

    def preview_skill(self, name, version=None, label=None, file="SKILL.md"):
        registry = self.registry()
        require(isinstance(file, str) and 0 < len(file) <= 256, "Invalid file selection")
        resolved, server_md5, data = registry.download(name, version, label)
        files = package.unpack(data)
        require(package.metadata(files["SKILL.md"])["name"] == name,
                "Resource identity differs from the package Skill name", "conflict")
        require(file in files, "Requested file is not part of the Skill package", "not_found")
        content = files[file]
        require(len(content) <= PREVIEW_BYTES, "File exceeds the install-free preview limit", "unsupported")
        try:
            text = content.decode()
        except UnicodeError:
            raise PluginError("unsupported", "Only UTF-8 text can be read without installing") from None
        return {"ref": self.reference("skill", name), "version": resolved, "serverMd5": server_md5, "file": file,
                "content": text, "files": [{"path": key, "bytes": len(value)} for key, value in sorted(files.items())],
                "route": "registry_preview", "saved": False, "installed": False,
                "hostLoaded": "not_claimed", "currentTurnTools": "not_claimed",
                "contentTrust": "untrusted_resource", "execution": "not_performed",
                "reuse": self.reuse_decision()}

    def trial_endpoint(self, resource_type, name, version, endpointIndex, auth):
        """Always re-resolve through the registry; a trial never accepts a raw URL."""
        found = self.discover(resource_type, name, version)
        require(type(endpointIndex) is int and 0 <= endpointIndex < len(found["endpoints"]),
                "Invalid endpoint selection")
        return found, found["endpoints"][endpointIndex], self.separate_downstream(auth_config(auth))

    def trial_tools(self, rpc):
        tools, cursor, seen = [], None, set()
        for _ in range(TRIAL_TOOL_PAGES):
            result = rpc.request("tools/list", {"cursor": cursor} if cursor else {})
            require(isinstance(result, dict) and isinstance(result.get("tools"), list),
                    "Invalid MCP tools response", "protocol")
            tools += result["tools"]
            require(len(tools) <= TRIAL_TOOL_LIMIT, "Tool catalogue exceeds the trial limit", "unsupported")
            cursor = result.get("nextCursor")
            if cursor is None:
                return tools
            require(isinstance(cursor, str) and cursor and cursor not in seen,
                    "Tool pagination cursor is invalid or repeated", "protocol")
            seen.add(cursor)
        raise PluginError("unsupported", "Tool catalogue needs more pages than the trial limit")

    def mcp_trial(self, name, version=None, endpointIndex=0, auth=None, tool=None, arguments=None):
        self.profile("call")
        found, selected, auth = self.trial_endpoint("mcp", name, version, endpointIndex, auth)
        base = {"ref": found["ref"], "version": found["version"], "endpoint": selected,
                "route": "registry_mcp_adapter", "saved": False, "hostLoaded": "not_claimed",
                "currentTurnTools": "not_claimed", "reuse": self.reuse_decision()}
        rpc = JsonRpc(selected["url"], auth)
        try:
            initialized = rpc.initialize_mcp()
            require("tools" in initialized.get("capabilities", {}), "Downstream does not declare tools", "unsupported")
            if tool is None:
                require(arguments is None, "Select a tool before sending arguments")
                return {**base, "tools": self.trial_tools(rpc), "realUse": "not_performed"}
            require(isinstance(tool, str) and 0 < len(tool) <= 128, "Invalid tool name")
            operation = self.store.operation("mcp_trial", found["ref"])
            # Records keep no task text, arguments, credentials or business response.
            operation.update(tool=tool, version=found["version"], inputDigest=digest(arguments or {}))
            self.store.save()
            try:
                result = rpc.request("tools/call", {"name": tool, "arguments": arguments or {}}, mutation=True)
            except PluginError as exc:
                operation.update(status="result_unknown" if exc.kind == "result_unknown" else "failed",
                                 toolError=exc.kind)
                self.store.save()
                return {**base, "operationId": operation["id"], "status": operation["status"],
                        "error": exc.result(), "realUse": "failed"}
            operation["status"] = "completed"
            self.store.save()
            return {**base, "operationId": operation["id"], "realUse": "completed", "result": result}
        finally:
            rpc.close_mcp()

    def agent_trial(self, name, text, version=None, endpointIndex=0, auth=None):
        self.profile("call")
        require(isinstance(text, str) and 0 < len(text) <= TRIAL_TEXT_LIMIT, "Invalid Agent message")
        found, selected, auth = self.trial_endpoint("agent", name, version, endpointIndex, auth)
        item = {"id": digest(found["ref"]), "ref": found["ref"], "context": digest(self.profile()),
                "endpoint": selected, "auth": auth, "version": found["version"],
                "downstreamContext": self.store.authorization_context(auth), "status": "trial_not_saved"}
        return {**self.send_agent(item, text), "ref": found["ref"], "version": found["version"],
                "endpoint": selected, "route": "registry_a2a_adapter", "saved": False,
                "reuse": self.reuse_decision()}
