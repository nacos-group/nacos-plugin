# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Real loopback HTTP MCP/A2A peers with deterministic business results."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading
import uuid


class Peers:
    def __init__(self):
        self.calls = []
        self.tasks = {}
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def send(self, status, value=None):
                data = json.dumps(value).encode() if value is not None else b""
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_DELETE(self):
                self.send(204)

            def do_POST(self):
                if (self.headers.get("Authorization") != "Bearer " + os.environ["NACOS_IT_DOWNSTREAM_TOKEN"]
                        or self.headers.get("accessToken")):
                    self.send(401)
                    return
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                method, params = payload["method"], payload.get("params", {})
                owner.calls.append(method)
                if "id" not in payload:
                    self.send(202)
                    return
                if method == "initialize":
                    result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                              "serverInfo": {"name": "integration-peer", "version": "1.0.0"}}
                elif method == "tools/list":
                    result = {"tools": [{"name": "echo", "description": "Echo a synthetic test message",
                                         "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}}]}
                elif method == "tools/call":
                    result = {"content": [{"type": "text", "text": params["arguments"]["text"]}], "isError": False}
                elif method == "message/send":
                    identifier = uuid.uuid4().hex
                    result = {"kind": "task", "id": identifier, "contextId": "integration",
                              "status": {"state": "working"}}
                    owner.tasks[identifier] = result
                elif method in ("tasks/get", "tasks/cancel"):
                    result = owner.tasks[params["id"]]
                    if method == "tasks/cancel":
                        result["status"] = {"state": "canceled"}
                else:
                    self.send(200, {"jsonrpc": "2.0", "id": payload["id"],
                                    "error": {"code": -32601, "message": "Unknown test method"}})
                    return
                self.send(200, {"jsonrpc": "2.0", "id": payload["id"], "result": result})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port
        self.url = f"http://127.0.0.1:{self.port}"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


class ResponseLossProxy:
    """Forward to real Nacos, then truncate exactly one completed upload response."""
    def __init__(self, upstream):
        from http.client import HTTPConnection
        from urllib.parse import urlsplit
        parsed = urlsplit(upstream)
        assert parsed.hostname == "127.0.0.1"
        owner = self
        self.uploads = 0

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def forward(self):
                data = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                headers = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "connection")}
                connection = HTTPConnection(parsed.hostname, parsed.port, timeout=20)
                try:
                    connection.request(self.command, self.path, body=data or None, headers=headers)
                    response = connection.getresponse()
                    body = response.read()
                    lose = self.command == "POST" and urlsplit(self.path).path.endswith("/skills/upload")
                    if lose:
                        owner.uploads += 1
                        lose = owner.uploads == 1 and response.status == 200
                    self.send_response(response.status)
                    for key, value in response.getheaders():
                        if key.lower() not in ("connection", "transfer-encoding", "content-length"):
                            self.send_header(key, value)
                    self.send_header("Content-Length", str(len(body) + 16 if lose else len(body)))
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.wfile.write(b"{" if lose else body)
                    self.close_connection = True
                finally:
                    connection.close()

            do_GET = do_POST = do_PUT = do_DELETE = forward

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}" + parsed.path

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
