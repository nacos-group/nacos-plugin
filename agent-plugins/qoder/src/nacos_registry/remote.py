# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Downstream orchestration; discovery is never itself execution authority."""
import copy
import os
import time

from .downstream import JsonRpc, auth_config, endpoints
from .errors import PluginError, require
from .store import digest, new_id


class RemoteMixin:
    def discover(self, resourceType, name, version=None):
        require(resourceType in ("mcp", "agent"), "Unsupported resource type")
        detail = self.registry().discover(resourceType, name, version)
        return {"ref": self.reference(resourceType, name), "version": detail.get("version"),
                "description": detail.get("description"), "endpoints": endpoints(resourceType, detail), "checkedAt": time.time()}

    def connection_plan(self, resourceType, name, auth=None, version=None, endpointIndex=0, discoveryReuse=None):
        require(resourceType == "agent", "Agent binding required")
        self.profile("call")
        self.check_discovery_reuse(discoveryReuse)
        found = self.discover(resourceType, name, version)
        require(isinstance(endpointIndex, int) and 0 <= endpointIndex < len(found["endpoints"]), "Invalid endpoint selection")
        selected = found["endpoints"][endpointIndex]
        auth = auth_config(auth)
        if auth["type"] == "bearer":
            refs = [value for field in ("clientAuth", "adminAuth") for key, value in self.profile()[field].items() if key.endswith("Env")]
            require(auth["tokenEnv"] not in refs, "Use a separate credential reference for the downstream service")
            token = os.environ.get(auth["tokenEnv"])
            require(not token or token not in self.nacos_secret_values(), "Use a separate downstream credential value")
        return self.plan("bind_agent", found["ref"], connectionId=digest(found["ref"]),
                         endpoint=selected, auth=auth, version=found["version"],
                         discoveryReuse=discoveryReuse,
                         downstreamContext=self.store.authorization_context(auth),
                         previous=copy.deepcopy(self.data["connections"].get(digest(found["ref"]))))

    def recheck_connection(self, item):
        require(item["context"] == digest(self.profile()), "Connection belongs to another context", "permission")
        require(item.get("downstreamContext") == self.store.authorization_context(item["auth"]),
                "Connection credentials or configuration changed; create a new authorized binding", "conflict")
        found = self.discover(item["ref"]["resourceType"], item["ref"]["name"], item["version"])
        require(item["endpoint"] in found["endpoints"], "Endpoint changed or unavailable; create a new connection plan", "conflict")

    def apply_bind_agent(self, p, operation):
        self.recheck_connection(p)
        require(self.data["connections"].get(p["connectionId"]) == p["previous"], "Connection changed; replan Agent binding", "conflict")
        connection = {k: p[k] for k in ("ref", "context", "endpoint", "auth", "version", "downstreamContext")}
        connection.update(id=p["connectionId"], status="configured_unverified")
        self.data["connections"][connection["id"]] = connection
        return connection

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
            return {"connectionId": connectionId, "transport": "connected", "hostLoaded": "unverified", "realUse": "unverified", **result}
        finally:
            rpc.close_mcp()

    def agent_send(self, connectionId, text):
        item = self.connection(connectionId, "agent")
        require(isinstance(text, str) and 0 < len(text) <= 65536, "Invalid Agent message")
        return self.send_agent(item, text)

    def send_agent(self, item, text):
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
        current = self.data["connections"].get(item["id"])
        if current and all(current[key] == item[key] for key in ("ref", "version", "endpoint")):
            item = copy.deepcopy(current)
        require(item.get("downstreamContext") == self.store.authorization_context(item["auth"]),
                "Task credentials changed; authorize a binding to the original task endpoint", "conflict")
        task["connection"] = item
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
