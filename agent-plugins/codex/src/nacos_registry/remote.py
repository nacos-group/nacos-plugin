# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Downstream orchestration; discovery is never itself execution authority."""
import copy
import time

from .downstream import JsonRpc, auth_config, endpoints
from .errors import PluginError, require
from .hosts import codex
from .hosts import native
from .store import atomic_write, digest, new_id


class RemoteMixin:
    def discover(self, resourceType, name, version=None):
        require(resourceType in ("mcp", "agent"), "Unsupported resource type")
        detail = self.registry().discover(resourceType, name, version)
        return {"ref": self.reference(resourceType, name), "version": detail.get("version"),
                "description": detail.get("description"), "endpoints": endpoints(resourceType, detail), "checkedAt": time.time()}

    def trial_connection(self, resourceType, name, auth=None, version=None, endpointIndex=0):
        self.profile("call")
        found = self.discover(resourceType, name, version)
        require(isinstance(endpointIndex, int) and 0 <= endpointIndex < len(found["endpoints"]), "Invalid endpoint selection")
        selected = found["endpoints"][endpointIndex]
        auth = auth_config(auth)
        if auth["type"] == "bearer":
            refs = [value for field in ("clientAuth", "adminAuth") for key, value in self.profile()[field].items() if key.endswith("Env")]
            require(auth["tokenEnv"] not in refs, "Use a separate credential reference for the downstream service")
        return {"id": digest(found["ref"]), "ref": found["ref"], "context": digest(self.profile()),
                "endpoint": selected, "auth": auth, "version": found["version"]}

    def connection_plan(self, resourceType, name, auth=None, version=None, endpointIndex=0, discoveryReuse=None):
        self.check_discovery_reuse(discoveryReuse)
        item = self.trial_connection(resourceType, name, auth, version, endpointIndex)
        connection_id = item["id"]
        fields = {"connectionId": connection_id, "endpoint": item["endpoint"], "auth": item["auth"],
                  "version": item["version"], "discoveryReuse": discoveryReuse}
        if resourceType == "agent":
            return self.plan("bind_agent", item["ref"], **fields)
        self.profile("install")
        config_path = self.profile().get("codexConfig")
        require(config_path, "Configure the target Codex config.toml path first", "configuration")
        original = codex.read_config(config_path)
        key = codex.connection_key(name, connection_id)
        block = codex.connection_block(key, item["endpoint"]["url"], item["auth"])
        previous = self.data["connections"].get(connection_id)
        codex.replace_connection(original, key, block, previous)
        effects = ["Persist the owned MCP block for reuse; request native refresh separately and verify the current conversation"]
        if previous and previous["configKey"] != key:
            effects.append(f"Rename managed MCP server {previous['configKey']} to {key}; loaded conversations may retain the old name until refresh")
        return self.plan("mcp_config", item["ref"], **fields, configPath=config_path, configBaseline=codex.fingerprint(original),
                         configBlock=block, configKey=key, previous=copy.deepcopy(previous), preview=block,
                         effects=effects)

    def recheck_connection(self, item):
        require(item["context"] == digest(self.profile()), "Connection belongs to another context", "permission")
        found = self.discover(item["ref"]["resourceType"], item["ref"]["name"], item["version"])
        require(item["endpoint"] in found["endpoints"], "Endpoint changed or unavailable; create a new connection plan", "conflict")

    def apply_bind_agent(self, p, operation):
        self.recheck_connection(p)
        connection = {k: p[k] for k in ("ref", "context", "endpoint", "auth", "version")}
        connection.update(id=p["connectionId"], status="configured_unverified")
        self.data["connections"][connection["id"]] = connection
        return connection

    def apply_mcp_config(self, p, operation):
        self.recheck_connection(p)
        current = codex.read_config(p["configPath"])
        require(codex.fingerprint(current) == p["configBaseline"], "Codex configuration changed; replan", "conflict")
        previous = p.get("previous")
        updated = codex.replace_connection(current, p["configKey"], p["configBlock"], previous)
        identifier = new_id()
        atomic_write(self.store.artifact(identifier, ".toml"), current)
        operation.update(configBackup=identifier, configPath=p["configPath"], configAfter=codex.fingerprint(updated))
        self.store.save()
        atomic_write(p["configPath"], updated)
        connection = {k: p[k] for k in ("ref", "context", "endpoint", "auth", "version", "configBlock", "configKey", "configPath")}
        connection.update(id=p["connectionId"], status="pending_host_reload")
        self.data["connections"][connection["id"]] = connection
        return connection

    def disconnect_plan(self, connectionId):
        self.profile("install")
        item = self.data["connections"].get(connectionId)
        require(item and item["context"] == digest(self.profile()), "Connection not found in current context", "not_found")
        fields = {"connectionId": connectionId, "previous": copy.deepcopy(item)}
        if item["ref"]["resourceType"] == "mcp":
            current = codex.read_config(item["configPath"])
            codex.replace_block(current, item["configKey"], "", item["configBlock"])
            fields.update(configPath=item["configPath"], configBaseline=codex.fingerprint(current), configKey=item["configKey"])
        return self.plan("disconnect", item["ref"], **fields, effects=["Remove only the owned local connection; remote service is unchanged"])

    def apply_disconnect(self, p, operation):
        if p["ref"]["resourceType"] == "mcp":
            current = codex.read_config(p["configPath"])
            require(codex.fingerprint(current) == p["configBaseline"], "Configuration changed; replan", "conflict")
            updated = codex.replace_block(current, p["configKey"], "", p["previous"]["configBlock"])
            identifier = new_id()
            atomic_write(self.store.artifact(identifier, ".toml"), current)
            operation.update(configBackup=identifier, configPath=p["configPath"], configAfter=codex.fingerprint(updated))
            self.store.save()
            atomic_write(p["configPath"], updated)
        self.data["connections"].pop(p["connectionId"], None)
        return {"status": "disconnected", "hostState": "pending_reload", "remoteChanged": False}

    def recover_config(self, op, plan):
        current = codex.read_config(op["configPath"])
        before = self.store.artifact(op["configBackup"], ".toml").read_bytes()
        require(codex.fingerprint(current) in (op["configAfter"], codex.fingerprint(before)), "Configuration changed after operation; preserve it", "conflict")
        previous = plan.get("previous")
        if previous:
            self.recheck_connection(previous)
        atomic_write(op["configPath"], before)
        if previous:
            self.data["connections"][previous["id"]] = {**previous, "status": "pending_host_reload"}
        else:
            self.data["connections"].pop(plan["connectionId"], None)
        op["status"] = "recovered"
        self.store.save()
        return op

    def connection(self, connectionId, kind):
        self.profile("call")
        item = self.data["connections"].get(connectionId)
        require(item and item["ref"]["resourceType"] == kind, "Connection not found", "not_found")
        self.recheck_connection(item)
        return item

    def mcp_probe(self, connectionId):
        item = self.connection(connectionId, "mcp")
        rpc = JsonRpc(item["endpoint"]["url"], item["auth"])
        try:
            initialized = rpc.initialize_mcp()
            require("tools" in initialized.get("capabilities", {}), "Downstream does not declare tools", "unsupported")
            result = rpc.request("tools/list", {})
            require(isinstance(result, dict) and isinstance(result.get("tools"), list), "Invalid MCP tools response", "protocol")
            item.update(probeStatus="tools_discovered", checkedAt=time.time())
            self.store.save()
            # Remote tool metadata cannot certify local loading or a business call.
            return {**result, "connectionId": connectionId, "transport": "connected",
                    "nativeServerName": item["configKey"], "hostLoaded": "unverified", "realUse": "unverified",
                    "loadingHint": "Check this server's tools in the current conversation. If absent, use Codex Settings > MCP servers > Restart, then recheck the current conversation's tool catalog. If still unavailable, try a new local conversation. This probe only lists tools; repeating it does not load them."}
        finally:
            rpc.close_mcp()

    def mcp_trial(self, name, version=None, endpointIndex=0, auth=None, tool=None, arguments=None):
        """Registry-bound MCP calls without saving a native connection.

        This is adapter-mediated MCP, never evidence of native Codex loading.
        Each request re-resolves visibility/endpoint and checks the tool catalog.
        """
        item = self.trial_connection("mcp", name, auth, version, endpointIndex)
        allowed = lambda tool: codex.trial_tool_allowed(self.profile().get("codexConfig"), item["endpoint"]["url"], tool)
        require(allowed(tool), "Native server/tool policy does not permit this trial", "permission")
        require(tool is not None or arguments is None, "Choose a tool before passing arguments")
        require(arguments is None or isinstance(arguments, dict), "Tool arguments must be an object")
        rpc = JsonRpc(item["endpoint"]["url"], item["auth"])
        operation = None
        try:
            initialized = rpc.initialize_mcp()
            require("tools" in initialized.get("capabilities", {}), "Downstream does not declare tools", "unsupported")
            catalog, cursor, seen = [], None, set()
            for _ in range(5):
                page = rpc.request("tools/list", {"cursor": cursor} if cursor else {})
                require(isinstance(page, dict) and isinstance(page.get("tools"), list), "Invalid MCP tool catalog", "protocol")
                catalog.extend(page["tools"])
                require(len(catalog) <= 500, "MCP tool catalog exceeds trial limit", "unsupported")
                cursor = page.get("nextCursor")
                if not cursor: break
                require(isinstance(cursor, str) and cursor not in seen, "Invalid MCP catalog cursor", "protocol")
                seen.add(cursor)
            else:
                require(False, "MCP tool catalog exceeds trial page limit", "unsupported")
            base = {"ref": item["ref"], "version": item["version"], "route": "registry_mcp_adapter",
                    "saved": False, "hostLoaded": "not_claimed"}
            catalog = [t for t in catalog if isinstance(t, dict) and isinstance(t.get("name"), str) and allowed(t["name"])]
            if tool is None:
                return {**base, "tools": catalog, "realUse": "not_performed"}
            require(isinstance(tool, str) and any(isinstance(t, dict) and t.get("name") == tool for t in catalog),
                    "Selected MCP tool is not in the current catalog", "not_found")
            operation = self.store.operation("mcp_trial", item["ref"])
            operation.update(tool=tool, version=item["version"], inputDigest=digest(arguments or {}))
            self.store.save()
            result = rpc.request("tools/call", {"name": tool, "arguments": arguments or {}}, mutation=True)
            require(isinstance(result, dict) and isinstance(result.get("content"), list), "Invalid MCP tool result", "result_unknown")
            operation.update(status="completed", toolError=result.get("isError") is True)
            self.store.save()
            return {**base, "operationId": operation["id"], "realUse": "failed" if operation["toolError"] else "completed",
                    "result": result}
        except PluginError as exc:
            if operation:
                operation.update(status="result_unknown" if exc.kind == "result_unknown" else "failed", error=exc.result())
                self.store.save()
                return {"operationId": operation["id"], "status": operation["status"], "error": exc.result(),
                        "route": "registry_mcp_adapter", "saved": False, "hostLoaded": "not_claimed"}
            raise
        finally:
            rpc.close_mcp()

    def mcp_refresh(self, connectionId, threadId):
        item = self.connection(connectionId, "mcp")
        current = codex.read_config(item["configPath"])
        codex.replace_block(current, item["configKey"], item["configBlock"], item["configBlock"])
        return {"connectionId": connectionId, "nativeServerName": item["configKey"],
                **native.refresh(item["configKey"], threadId, item["configPath"])}

    def agent_trial(self, name, text, version=None, endpointIndex=0, auth=None):
        item = self.trial_connection("agent", name, auth, version, endpointIndex)
        return {**self.send_agent(item, text), "route": "registry_a2a_adapter", "saved": False}

    def agent_send(self, connectionId, text):
        item = self.connection(connectionId, "agent")
        return self.send_agent(item, text)

    def send_agent(self, item, text):
        require(isinstance(text, str) and 0 < len(text) <= 65536, "Invalid Agent message")
        operation = self.store.operation("agent_send", item["ref"])
        operation.update(endpoint=item["endpoint"], messageId=new_id(), inputDigest=digest(text))
        self.store.save()
        rpc = JsonRpc(item["endpoint"]["url"], item["auth"])
        try:
            result = rpc.request("message/send", {"message": {"kind": "message", "role": "user", "messageId": operation["messageId"], "parts": [{"kind": "text", "text": text}]},
                                                   "configuration": {"blocking": True}}, mutation=True)
            require(isinstance(result, dict) and result.get("kind") in ("task", "message"), "Unexpected A2A response", "result_unknown")
            task_id = result.get("id") if result["kind"] == "task" else None
            require(result["kind"] != "task" or isinstance(task_id, str) and task_id, "A2A task has no valid reference", "result_unknown")
            if task_id:
                local_id = new_id()
                self.data["tasks"][local_id] = {"id": local_id, "taskId": task_id, "connection": copy.deepcopy(item),
                                               "context": item["context"], "status": result.get("status", {}).get("state", "unknown"),
                                               "updatedAt": time.time(), "cancelRequested": False}
                operation.update(taskHandle=local_id, taskId=task_id, taskStatus=result.get("status", {}).get("state", "unknown"))
            operation["status"] = "completed"
            self.store.save()
            # Result content is returned to the caller, not written into operation logs.
            return {"operationId": operation["id"], "taskHandle": operation.get("taskHandle"), "result": result}
        except PluginError as exc:
            operation.update(status="result_unknown" if exc.kind == "result_unknown" else "failed", error=exc.result())
            self.store.save()
            return operation

    def agent_task(self, taskHandle, action="get"):
        self.profile("call")
        require(action in ("get", "cancel"), "Choose get or cancel")
        task = self.data["tasks"].get(taskHandle)
        require(task and task["context"] == digest(self.profile()), "Task not found in current context", "not_found")
        if action == "cancel":
            require(task.get("status") not in ("completed", "failed", "canceled", "rejected") and not task.get("cancelRequested"),
                    "Task is terminal or cancellation was already requested; query its state", "conflict")
        item = task["connection"]
        # Check current registry visibility, but keep the original endpoint for an in-flight task.
        self.registry().discover("agent", item["ref"]["name"], item["version"])
        rpc = JsonRpc(item["endpoint"]["url"], item["auth"])
        op = self.store.operation("agent_task_" + action, item["ref"])
        op["taskHandle"] = taskHandle
        if action == "cancel":
            task["cancelRequested"] = True
        self.store.save()
        try:
            result = rpc.request("tasks/" + action, {"id": task["taskId"]}, mutation=action == "cancel")
            require(isinstance(result, dict) and result.get("id") == task["taskId"], "Task response mismatch", "result_unknown" if action == "cancel" else "protocol")
            op.update(status="completed", taskId=task["taskId"], taskStatus=result.get("status", {}).get("state", "unknown"))
            task.update(status=op["taskStatus"], updatedAt=time.time())
            if action == "get" and task["status"] == "canceled":
                for previous in self.data["operations"].values():
                    if (previous.get("action") == "agent_task_cancel"
                            and previous.get("taskHandle") == taskHandle
                            and previous.get("status") in ("running", "result_unknown")
                            and self.operation_current(previous)):
                        previous.update(status="completed", reconciled=True, taskStatus="canceled")
            self.store.save()
            return {"operationId": op["id"], "taskHandle": taskHandle, "result": result}
        except PluginError as exc:
            if action == "cancel" and exc.kind != "result_unknown":
                task["cancelRequested"] = False
            op.update(status="result_unknown" if exc.kind == "result_unknown" else "failed", error=exc.result())
            self.store.save()
            return op
