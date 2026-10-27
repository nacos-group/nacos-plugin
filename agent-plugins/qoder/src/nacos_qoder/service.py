# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
import copy
import os
import re

from nacos_registry.downstream import auth_config
from nacos_registry.errors import require
from nacos_registry.service import Service as RegistryService
from nacos_registry.store import digest

ENTRY_PREFIX = "nacos_"


def entry_slug(name):
    """Keep the resource recognizable in the native connector list."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:32].strip("_")
    return slug or "resource"


def native_entry_name(ref):
    """Resource name plus a suffix derived from the full identity, so the same name in
    another registry or namespace never reuses the native connector key."""
    return ENTRY_PREFIX + entry_slug(ref["name"]) + "_" + digest(ref)[:12]


class Service(RegistryService):
    def status(self):
        base = super().status()
        storage = base["credentialStorage"]
        return {**base, "host": {
            "name": "Qoder", "execution": "local", "stateDirectory": str(self.store.root),
            "skillRefresh": "Ask the user to reload Skills in the current conversation, then confirm the Skill is listed; writing files does not prove loading",
            "mcpRegistration": "Use Qoder native connector management with user confirmation in the current conversation",
            "sameSessionLoading": {"skills": "user_reload_required", "mcp": "native_tool_mediated",
                                   "pluginCanRefresh": False, "restart": "not_permitted",
                                   "newConversation": "last_resort"},
            "loadEvidence": {"refreshAccepted": "host_reload_or_connector_result",
                             "runtimeConnected": "native_connector_query",
                             "currentTurnTools": "host_tool_discovery",
                             "businessCall": "separate_real_use"},
            "nativeEntryName": {"format": ENTRY_PREFIX + "<resource slug>_<12 hex of resource identity>",
                                "legacyFormat": ENTRY_PREFIX + "<20 hex of resource identity>",
                                "renameProvesReload": False},
            "resourceCenter": "not_implemented", "nativePageCapability": "not_verified", "pageCredentials": "not_supported",
            "credentialInput": "native_macos_dialog" if storage["input"] else "not_available",
            "credentialTransport": "dialog_to_plugin_process" if storage["available"] else "environment_references",
            "systemCredentialStore": "macos_keychain" if storage["backend"] else "not_available",
            "prompt": "not_supported", "agentSpec": "not_supported", "localAgentGateway": "not_supported"}}

    def connection_plan(self, resourceType, name, auth=None, version=None, endpointIndex=0, discoveryReuse=None):
        if resourceType == "agent":
            return super().connection_plan(resourceType, name, auth, version, endpointIndex, discoveryReuse)
        require(resourceType == "mcp", "Unsupported resource type")
        self.profile("call")
        self.profile("install")
        self.check_discovery_reuse(discoveryReuse)
        found = self.discover(resourceType, name, version)
        require(type(endpointIndex) is int and 0 <= endpointIndex < len(found["endpoints"]), "Invalid endpoint selection")
        selected = found["endpoints"][endpointIndex]
        auth = auth_config(auth)
        if auth["type"] == "bearer":
            refs = [value for field in ("clientAuth", "adminAuth")
                    for key, value in self.profile()[field].items() if key.endswith("Env")]
            require(auth["tokenEnv"] not in refs, "Use a separate downstream credential reference")
            token = os.environ.get(auth["tokenEnv"])
            require(not token or token not in self.nacos_secret_values(), "Use a separate downstream credential value")
        identifier = digest(found["ref"])
        previous = copy.deepcopy(self.data["connections"].get(identifier))
        registration = {"entryName": native_entry_name(found["ref"]),
                        "config": {"type": "http", "url": selected["url"]},
                        "authentication": auth, "status": "pending_user_confirmation"}
        saved_name = (previous or {}).get("hostRegistration", {}).get("entryName")
        if saved_name and saved_name != registration["entryName"]:
            registration["previousEntryName"] = saved_name
            registration["migration"] = ("Add the new entry, then remove the previous owned entry only after "
                                         "confirming ownership and the user agrees; never overwrite or delete silently")
        if auth["type"] == "bearer":
            registration["status"] = "requires_native_authentication"
        return self.plan("mcp_config", found["ref"], connectionId=identifier, endpoint=selected,
                         auth=auth, version=found["version"], hostRegistration=registration,
                         discoveryReuse=discoveryReuse,
                         downstreamContext=self.store.authorization_context(auth),
                         previous=previous,
                         effects=["Save a local binding only; register separately through Qoder native connector management",
                                  "Never copy Nacos credentials or store downstream secrets in connector JSON"])

    def mcp_probe(self, connectionId):
        result = super().mcp_probe(connectionId)
        registration = self.data["connections"][connectionId].get("hostRegistration", {})
        return {**result, "nativeEntryName": registration.get("entryName"),
                "loadingHint": "Register or reload the native connector in the current conversation, then confirm the "
                               "tools appear through host tool discovery; a downstream probe proves neither"}

    def apply_mcp_config(self, plan, operation):
        self.recheck_connection(plan)
        require(self.data["connections"].get(plan["connectionId"]) == plan["previous"],
                "Connection changed; replan registration", "conflict")
        item = {key: copy.deepcopy(plan[key]) for key in ("ref", "context", "endpoint", "auth", "version", "hostRegistration", "downstreamContext")}
        item.update(id=plan["connectionId"], status="pending_host_registration")
        self.data["connections"][item["id"]] = item
        return item

    def disconnect_plan(self, connectionId):
        self.profile("install")
        item = self.data["connections"].get(connectionId)
        require(item and item["context"] == digest(self.profile()), "Connection not found in this context", "not_found")
        fields = {"connectionId": connectionId, "previous": copy.deepcopy(item)}
        if item["ref"]["resourceType"] == "mcp":
            fields["hostRemoval"] = copy.deepcopy(item["hostRegistration"])
        return self.plan("disconnect", item["ref"], **fields,
                         effects=["Remove only the plugin binding; remove an owned native connector separately with user confirmation"])

    def apply_disconnect(self, plan, operation):
        item = self.data["connections"].get(plan["connectionId"])
        require(item == plan["previous"], "Connection changed; replan disconnect", "conflict")
        self.data["connections"].pop(plan["connectionId"])
        return {"status": "disconnected", "remoteChanged": False,
                "hostState": "pending_native_removal" if plan["ref"]["resourceType"] == "mcp" else "not_applicable",
                "hostRemoval": plan.get("hostRemoval")}
