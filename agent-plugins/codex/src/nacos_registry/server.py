# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Small stdio MCP endpoint. stdout contains only newline-delimited JSON-RPC."""
import json
import sys

from . import __version__
from .errors import PluginError, require
from .service import Service
from .ui import render_ui

STRING = {"type": "string"}
STRINGS = {"type": "array", "items": STRING}
BOOL = {"type": "boolean"}
INTEGER = {"type": "integer"}
UI_URI = "ui://nacos-ai-registry/resource-center-" + __version__ + ".html"
UI_TOOLS = {"open_center": "Nacos AI Registry", "open_center_panel": "资源中心"}
UI_RESOURCES = {"open_center": UI_URI,
                "open_center_panel": "ui://nacos-ai-registry/resource-center-panel-" + __version__ + ".html"}
UI_ENTRYPOINTS = {"open_center": "global", "open_center_panel": "thread"}


def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


AUTH = obj({"type": {"type": "string", "enum": ["none", "bearer"]}, "tokenEnv": STRING}, ["type"])
REGISTRY_AUTH = obj({"type": {"type": "string", "enum": ["none", "token", "login"]}, "tokenEnv": STRING, "usernameEnv": STRING, "passwordEnv": STRING}, ["type"])
PROFILE = obj({"id": STRING, "displayName": STRING, "identityId": STRING, "namespaceId": STRING,
               "clientUrl": STRING, "adminUrl": STRING, "clientAuth": REGISTRY_AUTH, "adminAuth": REGISTRY_AUTH,
               "allowedOperations": STRINGS, "scanRoots": STRINGS, "installRoots": STRINGS, "codexConfig": STRING},
              ["id", "identityId", "namespaceId", "clientUrl", "adminUrl", "allowedOperations"])

# Each mutation has a specific workflow entry; there is no arbitrary HTTP, command or path tool.
DEFINITIONS = {
    "open_center": ("Open the Nacos resource center with installed resources, search, owned Skills and configuration.", obj({})),
    "open_center_panel": ("Open the resource center alongside this conversation.", obj({})),
    "my_skills": ("List only Skills owned by the authenticated native Admin login. Does not infer ownership from local identity labels or visibility.", obj({"query": STRING, "page": INTEGER, "limit": INTEGER})),
    "upload_preview": ("Inspect selected local Skill filenames and sizes before authorizing a precheck transfer. No network access.", obj({"scanId": STRING, "candidateId": STRING}, ["scanId", "candidateId"])),
    "configure": ("Configure one registry, independent credential environment references and explicit local roots. Does not probe permissions or upload content.", obj({"profile": PROFILE}, ["profile"])),
    "status": ("Read local setup, installations, bindings and unfinished operations. Cached state does not prove current remote access.", obj({})),
    "diagnose": ("Read-only Client search probe. Does not create resources or test write permissions.", obj({})),
    "search": ("Find Skill/MCP/Agent candidates. Preserve opaque pagination; use exact reads before installation/calls.", obj({"query": STRING, "resourceTypes": STRINGS, "cursor": STRING, "limit": INTEGER, "tagsAll": STRINGS})),
    "scan": ("List Skill metadata only in configured, user-selected roots; no network transfer, scripts, recursive machine scan or package precheck.", obj({"roots": STRINGS})),
    "onboarding": ("Skip, complete or reopen setup without uploading resources.", obj({"action": {"type": "string", "enum": ["skip", "finish", "reopen"]}}, ["action"])),
    "select": ("Apply explicit ignore/track choices with per-item results. Neither choice uploads content.", obj({"scanId": STRING, "selections": {"type": "array", "items": obj({"candidateId": STRING, "action": {"type": "string", "enum": ["ignore", "track"]}}, ["candidateId", "action"])}}, ["scanId", "selections"])),
    "upload_plan": ("TRANSMITS the selected Skill ZIP to Admin precheck, after user authorization covers its files and destination. Creates a draft upload plan; does not publish. Explicitly select existing-resource binding or draft overwrite when needed.", obj({"scanId": STRING, "candidateId": STRING, "overwriteDraft": BOOL, "bindExisting": BOOL, "commitMessage": STRING}, ["scanId", "candidateId"])),
    "install_plan": ("Download an exact/label/default Skill, validate package, and prepare install/update changes without applying them. Preserves local modifications.", obj({"name": STRING, "installRoot": STRING, "version": STRING, "label": STRING}, ["name", "installRoot"])),
    "skill_status": ("Read authoritative Admin Skill lifecycle, review result, visibility and optional exact content hashes. Use for review polling and unknown-outcome reconciliation.", obj({"name": STRING, "version": STRING}, ["name"])),
    "publish_plan": ("Plan submit/publish for an exact Skill version and actual visibility. Submit MAY immediately publish without a matching pipeline. Reviewed does not mean approved.", obj({"name": STRING, "version": STRING, "action": {"type": "string", "enum": ["submit", "publish"]}}, ["name", "version", "action"])),
    "apply": ("Apply an authorized, reviewed plan after rechecking context and baselines. Can write files, upload drafts or publish as specified by the plan. Never blindly retry unknown results.", obj({"planId": STRING}, ["planId"])),
    "uninstall_plan": ("Prepare removal of an unchanged owned Skill; retain user modifications. Does not delete remote resources.", obj({"installationId": STRING}, ["installationId"])),
    "inspect_operation": ("Read operation outcome and recovery evidence; running after a crash may be incomplete or unknown.", obj({"operationId": STRING}, ["operationId"])),
    "reconcile": ("Reconcile an unknown upload/submit/publish by exact server state and content. Does not resend the write; unmatched outcomes remain unknown.", obj({"operationId": STRING, "version": STRING}, ["operationId"])),
    "disconnect_plan": ("Plan removal of a locally owned MCP/Agent connection. Retains unrelated configuration and remote services.", obj({"connectionId": STRING}, ["connectionId"])),
    "recover": ("Restore the previous authorized local Skill snapshot or undo a new installation. No remote publication rollback; refuses local changes.", obj({"operationId": STRING}, ["operationId"])),
    "verify_skill": ("Check exact remote readability and installed bytes. Does not claim host loading or real use.", obj({"installationId": STRING}, ["installationId"])),
    "discover": ("Resolve exact MCP/A2A details through Client API. Returns supported frontend endpoints; never executes.", obj({"resourceType": {"type": "string", "enum": ["mcp", "agent"]}, "name": STRING, "version": STRING}, ["resourceType", "name"])),
    "connection_plan": ("Plan a native Codex Streamable HTTP MCP connection or A2A 0.3.0 JSONRPC binding. Credentials are independent env references; no secrets from registry metadata are used.", obj({"resourceType": {"type": "string", "enum": ["mcp", "agent"]}, "name": STRING, "auth": AUTH, "version": STRING, "endpointIndex": INTEGER}, ["resourceType", "name"])),
    "mcp_probe": ("Authenticate to the selected MCP service and discover tools without invoking business tools. Native host loading and actual use need separate verification.", obj({"connectionId": STRING}, ["connectionId"])),
    "agent_send": ("SEND user-authorized text to the selected A2A Agent. Can cause remote effects. Returns message/task; failures can be unknown and must not be blindly retried.", obj({"connectionId": STRING, "text": STRING}, ["connectionId", "text"])),
    "agent_task": ("Get or cancel a known A2A task on its original endpoint. Cancellation does not reverse prior effects.", obj({"taskHandle": STRING, "action": {"type": "string", "enum": ["get", "cancel"]}}, ["taskHandle"])),
}
READ_ONLY = {"status", "diagnose", "search", "inspect_operation", "discover", "verify_skill", "mcp_probe", "skill_status", "my_skills", "upload_preview", *UI_TOOLS}

# UI callers supply a context fingerprint so a concurrent identity/configuration
# change cannot redirect an action to a different registry. Older callers remain compatible.
for _name, (_, _schema) in DEFINITIONS.items():
    if _name not in UI_TOOLS:
        _schema["properties"]["_context"] = {"type": "string", "description": "Expected context returned by nacos_status; reject if the connection changed."}
DEFINITIONS["upload_plan"][1]["properties"]["expectedContentHash"] = STRING


def validate(value, schema):
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int}
    require(type(value) is types[kind], "Tool argument type mismatch")
    if "enum" in schema: require(value in schema["enum"], "Invalid enum value")
    if kind == "object":
        require(set(schema.get("required", [])) <= set(value), "Required tool argument missing")
        require(set(value) <= set(schema["properties"]), "Unknown tool argument")
        for key, child in value.items(): validate(child, schema["properties"][key])
    if kind == "array":
        require(len(value) <= 500, "Array limit exceeded")
        for child in value: validate(child, schema["items"])
    if kind == "string": require(len(value) <= 131072, "String limit exceeded")


def tools_list():
    result = [{"name": "nacos_" + name, "description": description, "inputSchema": schema,
             "_meta": {"ui": {"visibility": ["app", "model"]}},
             "annotations": {"readOnlyHint": name in READ_ONLY, "destructiveHint": name not in READ_ONLY,
                             "idempotentHint": name in READ_ONLY, "openWorldHint": name not in {"status", "scan", "select", "onboarding", "inspect_operation", "upload_preview", *UI_TOOLS}}}
            for name, (description, schema) in DEFINITIONS.items()]
    for tool in result:
        name = tool["name"][6:]
        if name in UI_TOOLS:
            tool["title"] = UI_TOOLS[name]
            tool["_meta"]["ui"]["resourceUri"] = UI_RESOURCES[name]
            tool["_meta"]["openai/ui"] = {"entrypoints": [{"type": UI_ENTRYPOINTS[name]}]}
    return result


def serve(service=None, source=None, sink=None):
    service = service or Service()
    source, sink = source or sys.stdin, sink or sys.stdout
    # Plugin updates may remove this process's bundle. Keep its UI snapshot for
    # the lifetime of the connection, including pages opened after the update.
    ui_pages = {}
    for name, entrypoint in UI_ENTRYPOINTS.items():
        try:
            ui_pages[name] = render_ui(entrypoint)
        except (OSError, UnicodeError, ValueError):
            pass
    ui_unavailable = "Page assets could not be loaded. Restart Codex and open the resource center again from the current conversation."
    initialized = False
    while True:
        line = source.readline(2 * 1024 * 1024 + 1)
        if not line: break
        req, response = None, None
        try:
            require(len(line) <= 2 * 1024 * 1024, "MCP message limit exceeded")
            req = json.loads(line)
            require(isinstance(req, dict) and req.get("jsonrpc") == "2.0", "Invalid JSON-RPC request")
            if "id" not in req:
                continue
            method, params = req.get("method"), req.get("params", {})
            if method == "initialize":
                requested = params.get("protocolVersion")
                protocol = requested if requested in ("2024-11-05", "2025-03-26", "2025-06-18") else "2025-03-26"
                result = {"protocolVersion": protocol, "capabilities": {"tools": {}, "resources": {}}, "serverInfo": {"name": "nacos-ai-registry", "version": __version__}}
                initialized = True
            elif method == "ping": result = {}
            elif not initialized:
                raise PluginError("protocol", "Initialize before using tools")
            elif method == "tools/list": result = {"tools": tools_list()}
            elif method == "resources/list":
                result = {"resources": [{"uri": uri, "name": UI_TOOLS[name], "mimeType": "text/html;profile=mcp-app"}
                                        for name, uri in UI_RESOURCES.items()]}
            elif method == "resources/read":
                name = next((key for key, uri in UI_RESOURCES.items() if uri == params.get("uri")), None)
                if name is None:
                    response = {"jsonrpc": "2.0", "id": req["id"], "error": {
                        "code": -32002,
                        "message": "Page resource not found. Close the old page and invoke the resource center tool again."}}
                elif name not in ui_pages:
                    response = {"jsonrpc": "2.0", "id": req["id"], "error": {
                        "code": -32603, "message": ui_unavailable}}
                else:
                    result = {"contents": [{"uri": UI_RESOURCES[name], "mimeType": "text/html;profile=mcp-app",
                               "text": ui_pages[name],
                               "_meta": {"ui": {"csp": {"connectDomains": [], "resourceDomains": []}},
                                         "openai/ui": {"preferredDisplayMode": "fullscreen", "availableDisplayModes": ["inline", "fullscreen"]}}}]}
            elif method == "tools/call":
                name = params.get("name", "")
                require(name.startswith("nacos_") and name[6:] in DEFINITIONS, "Unknown MCP tool")
                name = name[6:]
                args = params.get("arguments", {})
                try:
                    validate(args, DEFINITIONS[name][1])
                    args = dict(args)
                    context = args.pop("_context", None)
                    if name in UI_TOOLS and name not in ui_pages:
                        raise PluginError("ui_unavailable", ui_unavailable)
                    value = {"status": "ready", "version": __version__, "entrypoint": UI_ENTRYPOINTS[name]} if name in UI_TOOLS else service.invoke(name, args, expected_context=context)
                    failed = isinstance(value, dict) and value.get("status") in ("failed", "result_unknown", "recovery_required")
                    result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}], "structuredContent": value, "isError": failed}
                except PluginError as exc:
                    result = {"content": [{"type": "text", "text": json.dumps(exc.result())}], "isError": True}
                except (OSError, ValueError, TypeError, KeyError, UnicodeError, AttributeError, RecursionError):
                    result = {"content": [{"type": "text", "text": '{"error":"local_failure","message":"Input or local state could not be processed; inspect the operation before retrying"}'}], "isError": True}
            else:
                response = {"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32601, "message": "Method not found"}}
            if response is None:
                response = {"jsonrpc": "2.0", "id": req["id"], "result": result}
        except (ValueError, PluginError, TypeError, KeyError):
            response = {"jsonrpc": "2.0", "id": req.get("id") if isinstance(req, dict) else None, "error": {"code": -32600, "message": "Invalid request"}}
        sink.write(json.dumps(response, ensure_ascii=False) + "\n")
        sink.flush()
