# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
import json
import sys

from nacos_registry.errors import PluginError, require
from nacos_registry.schema import DEFINITIONS, READ_ONLY, validate

from . import __version__
from .service import Service


def tools_list():
    return [{"name": "nacos_" + name, "description": description, "inputSchema": schema,
             "annotations": {"readOnlyHint": name in READ_ONLY, "destructiveHint": name not in READ_ONLY,
                             "idempotentHint": name in READ_ONLY,
                             "openWorldHint": name not in {"status", "scan", "select", "onboarding", "inspect_operation", "upload_preview", "credentials"}}}
            for name, (description, schema) in DEFINITIONS.items()]


def call_tool(service, name, arguments):
    require(isinstance(name, str) and name.startswith("nacos_") and name[6:] in DEFINITIONS, "Unknown MCP tool")
    action = name[6:]
    validate(arguments, DEFINITIONS[action][1])
    arguments = dict(arguments)
    context = arguments.pop("_context", None)
    value = service.invoke(action, arguments, expected_context=context)
    failed = isinstance(value, dict) and value.get("status") in ("failed", "result_unknown", "recovery_required")
    return {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}],
            "structuredContent": value, "isError": failed}


def serve(service=None, source=None, sink=None):
    service = service if service is not None else Service()
    source, sink = source or sys.stdin, sink or sys.stdout
    initialized = False
    while True:
        line = source.readline(2 * 1024 * 1024 + 1)
        if not line:
            break
        request = None
        try:
            require(len(line) <= 2 * 1024 * 1024, "MCP message limit exceeded")
            request = json.loads(line)
            require(isinstance(request, dict) and request.get("jsonrpc") == "2.0", "Invalid JSON-RPC request")
            if "id" not in request:
                continue
            method, params = request.get("method"), request.get("params", {})
            require(isinstance(params, dict), "Invalid JSON-RPC parameters")
            if method == "initialize":
                requested = params.get("protocolVersion")
                protocol = requested if requested in ("2024-11-05", "2025-03-26", "2025-06-18") else "2025-03-26"
                result = {"protocolVersion": protocol, "capabilities": {"tools": {}},
                          "serverInfo": {"name": "nacos-ai-registry-qoder", "version": __version__}}
                initialized = True
            elif method == "ping":
                result = {}
            elif not initialized:
                raise PluginError("protocol", "Initialize before using tools")
            elif method == "tools/list":
                result = {"tools": tools_list()}
            elif method == "tools/call":
                try:
                    result = call_tool(service, params.get("name"), params.get("arguments", {}))
                except PluginError as exc:
                    result = {"content": [{"type": "text", "text": json.dumps(exc.result())}], "isError": True}
                except (OSError, ValueError, TypeError, KeyError, UnicodeError, AttributeError, RecursionError):
                    result = {"content": [{"type": "text", "text": '{"error":"local_failure","message":"Inspect local state before retrying; raw diagnostics omitted"}'}], "isError": True}
            else:
                response = {"jsonrpc": "2.0", "id": request["id"], "error": {"code": -32601, "message": "Method not found"}}
                sink.write(json.dumps(response) + "\n")
                sink.flush()
                continue
            response = {"jsonrpc": "2.0", "id": request["id"], "result": result}
        except (ValueError, PluginError, TypeError, KeyError):
            response = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                        "error": {"code": -32600, "message": "Invalid request"}}
        sink.write(json.dumps(response, ensure_ascii=False) + "\n")
        sink.flush()
