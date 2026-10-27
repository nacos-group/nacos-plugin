# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
from .errors import require

STRING = {"type": "string"}
STRINGS = {"type": "array", "items": STRING}
BOOL = {"type": "boolean"}
INTEGER = {"type": "integer"}


def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


AUTH = obj({"type": {"type": "string", "enum": ["none", "bearer"]}, "tokenEnv": STRING}, ["type"])
REGISTRY_AUTH = obj({"type": {"type": "string", "enum": ["none", "token", "login"]},
                     "source": {"type": "string", "enum": ["keychain", "environment"],
                                "description": "keychain (recommended, local macOS): enter later with nacos_credentials; environment: advanced process variable references"},
                     "tokenEnv": STRING, "usernameEnv": STRING, "passwordEnv": STRING}, ["type"])
PROFILE = obj({"id": STRING, "displayName": STRING, "identityId": STRING, "namespaceId": STRING,
               "clientUrl": STRING, "adminUrl": STRING,
               "adminMode": {"type": "string", "enum": ["shared", "independent"]},
               "clientAuth": REGISTRY_AUTH, "adminAuth": REGISTRY_AUTH,
               "allowedOperations": STRINGS, "scanRoots": STRINGS, "installRoots": STRINGS})

DEFINITIONS = {
    "status": ("Read local Qoder setup, personal .qoder/skills defaults, configuration revision, non-sensitive Client/Admin credential readiness and capability limits. status.context includes the configuration revision and current credential state. Does not scan files or prove remote access or host loading.", obj({})),
    "configure": ("Save a nonsecret Nacos profile, separately from diagnose access checks. namespaceId public is the Nacos default namespace ID. Authentication uses source keychain (recommended; enter values afterwards with nacos_credentials) or advanced environment variable references. A new profile needs namespaceId, clientUrl and allowedOperations; reconfiguration may send only confirmed changes and preserves omitted fields. Saved Keychain entries survive only when connection, identity, target, auth type and purpose are unchanged. Required expectedRevision prevents overwriting newer configuration. Environment credential reuse and adding Qoder default roots require explicit opt-in. Never accepts credentials or writes Qoder connector settings.", obj({"profile": PROFILE, "expectedRevision": INTEGER, "authorizeCredentialReuse": BOOL, "addDefaultRoots": BOOL}, ["profile", "expectedRevision"])),
    "credentials": ("Enter or clear Keychain-backed Client/Admin credentials for the saved profile. enter opens a native macOS dialog from the local plugin process (username then hidden password, or hidden token), stores the values only in a non-synchronizable login Keychain item and saves an opaque reference; takes effect without restarting Qoder. Values never appear in chat, tool arguments, results or plugin files. Ask the user before calling; the dialog waits for them. cancelled/timed_out/empty save nothing. clear removes only the plugin-owned entry. Requires the latest status context.", obj({"action": {"type": "string", "enum": ["enter", "clear"]}, "surface": {"type": "string", "enum": ["client", "admin"]}}, ["action", "surface"])),
    "diagnose": ("Persist a redacted, current-context diagnostic result from a read-only Client search probe, separately from configure profile saving. Does not save configuration, create resources or test write permissions.", obj({})),
    "search": ("Find Skill/MCP/Agent candidates. Preserve opaque pagination; use exact reads before installation/calls.", obj({"query": STRING, "resourceTypes": STRINGS, "cursor": STRING, "limit": INTEGER, "tagsAll": STRINGS})),
    "my_skills": ("List only Skills owned by the authenticated native Admin login. Does not infer ownership from local identity labels or visibility.", obj({"query": STRING, "page": INTEGER, "limit": INTEGER})),
    "scan": ("List Skill metadata only in configured, user-selected roots; no network transfer, scripts, recursive machine scan or package precheck.", obj({"roots": STRINGS})),
    "onboarding": ("Skip, complete or reopen the current-context inventory without uploading resources. Completion requires a current scan and an explicit ignore/track/explicit choice for every candidate; only terminal inventory can be reopened.", obj({"action": {"type": "string", "enum": ["skip", "finish", "reopen"]}}, ["action"])),
    "select": ("Apply explicit ignore/track choices with per-item results. Neither choice uploads content.", obj({"scanId": STRING, "selections": {"type": "array", "items": obj({"candidateId": STRING, "action": {"type": "string", "enum": ["ignore", "track"]}}, ["candidateId", "action"])}}, ["scanId", "selections"])),
    "upload_preview": ("Inspect selected local Skill filenames and sizes before authorizing a precheck transfer. No network access.", obj({"scanId": STRING, "candidateId": STRING}, ["scanId", "candidateId"])),
    "upload_plan": ("TRANSMITS the selected Skill ZIP to Admin precheck after user authorization covers its files and destination. Creates a draft upload plan, not publication. Explicitly select existing-resource binding or draft overwrite when needed.", obj({"scanId": STRING, "candidateId": STRING, "overwriteDraft": BOOL, "bindExisting": BOOL, "commitMessage": STRING, "expectedContentHash": STRING}, ["scanId", "candidateId"])),
    "install_plan": ("Download an exact/label/default Skill, validate its package and prepare install/update changes without applying them. Preserves local modifications.", obj({"name": STRING, "installRoot": STRING, "version": STRING, "label": STRING}, ["name", "installRoot"])),
    "skill_status": ("Read authoritative Admin Skill lifecycle, review result, visibility and optional exact content hashes. Use for review polling and unknown-outcome reconciliation.", obj({"name": STRING, "version": STRING}, ["name"])),
    "publish_plan": ("Plan submit/publish for an exact Skill version and actual visibility. Submit MAY immediately publish without a matching pipeline. Reviewed does not mean approved.", obj({"name": STRING, "version": STRING, "action": {"type": "string", "enum": ["submit", "publish"]}}, ["name", "version", "action"])),
    "apply": ("Apply an authorized, reviewed plan after rechecking context and baselines. Can write Skill files, upload drafts, publish, or save a local connection binding. Native Qoder connector registration is separate. Never blindly retry unknown results.", obj({"planId": STRING}, ["planId"])),
    "uninstall_plan": ("Prepare removal of an unchanged owned Skill; retain user modifications. Does not delete remote resources.", obj({"installationId": STRING}, ["installationId"])),
    "inspect_operation": ("Read operation outcome and recovery evidence; running after a crash may be incomplete or unknown.", obj({"operationId": STRING}, ["operationId"])),
    "reconcile": ("Reconcile an unknown upload/submit/publish by exact server state and content. Does not resend the write; unmatched outcomes remain unknown.", obj({"operationId": STRING, "version": STRING}, ["operationId"])),
    "recover": ("Restore the previous authorized local Skill snapshot or undo a new installation. No remote publication rollback; refuses local changes.", obj({"operationId": STRING}, ["operationId"])),
    "verify_skill": ("Check exact remote readability and installed bytes. Does not claim host loading or real use.", obj({"installationId": STRING}, ["installationId"])),
    "discover": ("Resolve exact MCP/A2A details through Client API. Returns supported frontend endpoints; never executes.", obj({"resourceType": {"type": "string", "enum": ["mcp", "agent"]}, "name": STRING, "version": STRING}, ["resourceType", "name"])),
    "connection_plan": ("Plan a local HTTP MCP or A2A 0.3.0 JSONRPC binding. MCP registration is a separate Qoder native confirmation step; bearer authentication must use a native secure mechanism.", obj({"resourceType": {"type": "string", "enum": ["mcp", "agent"]}, "name": STRING, "auth": AUTH, "version": STRING, "endpointIndex": INTEGER}, ["resourceType", "name"])),
    "disconnect_plan": ("Plan removal of a local binding, returning the exact native connector removal target if applicable. Does not delete native Qoder connectors or remote services.", obj({"connectionId": STRING}, ["connectionId"])),
    "mcp_probe": ("Authenticate to the selected MCP service and discover tools without invoking business tools. Native host loading and actual use need separate verification.", obj({"connectionId": STRING}, ["connectionId"])),
    "agent_send": ("SEND user-authorized text to the selected A2A Agent. Can cause remote effects. Returns message/task; failures can be unknown and must not be blindly retried.", obj({"connectionId": STRING, "text": STRING}, ["connectionId", "text"])),
    "agent_task": ("Get or cancel a known A2A task on its original endpoint. Cancellation does not reverse prior effects.", obj({"taskHandle": STRING, "action": {"type": "string", "enum": ["get", "cancel"]}}, ["taskHandle"])),
}
READ_ONLY = {"status", "diagnose", "search", "inspect_operation", "discover", "verify_skill", "mcp_probe", "skill_status", "my_skills", "upload_preview"}
for _, schema in DEFINITIONS.values():
    schema["properties"]["_context"] = {"type": "string", "description": "Expected status.context returned by nacos_status, including the configuration revision and current credential state; reject if either or the profile changed."}
DEFINITIONS["onboarding"][1]["required"].append("_context")
DEFINITIONS["credentials"][1]["required"].append("_context")


def validate(value, schema):
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int}
    require(type(value) is types[kind], "Tool argument type mismatch")
    if "enum" in schema:
        require(value in schema["enum"], "Invalid enum value")
    if kind == "object":
        require(set(schema.get("required", [])) <= set(value), "Required tool argument missing")
        require(set(value) <= set(schema["properties"]), "Unknown tool argument")
        for key, child in value.items():
            validate(child, schema["properties"][key])
    if kind == "array":
        require(len(value) <= 500, "Array limit exceeded")
        for child in value:
            validate(child, schema["items"])
    if kind == "string":
        require(len(value) <= 131072, "String limit exceeded")
