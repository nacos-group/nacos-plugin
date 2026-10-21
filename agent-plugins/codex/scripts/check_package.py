#!/usr/bin/env python3
# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Inspect and run the final package without site-packages or the source checkout."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import zipfile

ROOT = Path(__file__).resolve().parents[1]
version = json.loads((ROOT / "plugin.json").read_text())["version"]
archive_path = ROOT / "dist" / f"nacos-ai-registry-{version}.zip"
checksum = archive_path.with_suffix(".zip.sha256").read_text().split()[0]
assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == checksum


def check_document_links(root):
    for document in root.rglob("*.md"):
        for link in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", document.read_text()):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", link) or link.startswith("#"):
                continue
            target = (document.parent / link.split("#", 1)[0]).resolve()
            assert target.is_relative_to(root) and target.exists(), (document, link)


with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder).resolve()
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        assert "plugin.json" in names and "server/nacos-registry.pyz" in names
        assert not any("__pycache__" in x or "state.json" in x or "marketplace.json" in x for x in names)
        for name in names:
            assert not name.startswith("/") and ".." not in Path(name).parts
        archive.extractall(folder)
    manifest = json.loads((folder / "plugin.json").read_text())
    overlay = json.loads((folder / ".codex-plugin/plugin.json").read_text())
    assert manifest["version"] == overlay["version"] == version
    assert len(manifest["extensions"]["com.openai"]["interface"]["shortDescription"]) <= 30
    assert (folder / manifest["extensions"]["com.openai"]["onboardingSkill"]).is_file()
    native = json.loads((folder / manifest["extensions"]["com.openai"]["mcpServers"]).read_text())["mcpServers"]["nacos-ai-registry"]
    portable = json.loads((folder / "mcp.json").read_text())["mcpServers"]["nacos-ai-registry"]
    assert {k: native[k] for k in ("command", "args", "cwd")} == {k: portable[k] for k in ("command", "args", "cwd")}
    assert "env" not in native and "NACOS_PLUGIN_HOME" in native["env_vars"]
    assert all(re.fullmatch(r"NACOS_PLUGIN_[A-Z_]+", name) for name in native["env_vars"])
    check_document_links(folder)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "NACOS_PLUGIN_HOME")}
    result = subprocess.run([sys.executable, "-I", "-S", str(folder / "server/nacos-registry.pyz"), "--state-dir", str(folder / "state"), "status"], cwd=folder, env=env, check=True, capture_output=True, text=True)
    assert json.loads(result.stdout)["profile"] is None
    calls = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
    result = subprocess.run([sys.executable, "-I", "-S", str(folder / "server/nacos-registry.pyz"), "--state-dir", str(folder / "state"), "serve"], input="\n".join(map(json.dumps, calls)) + "\n", cwd=folder, env=env, check=True, capture_output=True, text=True)
    responses = [json.loads(x) for x in result.stdout.splitlines()]
    assert responses[0]["result"]["serverInfo"]["version"] == version
    assert any(x["name"] == "nacos_scan" for x in responses[1]["result"]["tools"])
    ui_tools = [x for x in responses[1]["result"]["tools"] if x["name"] in ("nacos_open_center", "nacos_open_center_panel")]
    assert len(ui_tools) == len({t["_meta"]["ui"]["resourceUri"] for t in ui_tools}) == 2
    for i, tool in enumerate(ui_tools, 3):
        calls.append({"jsonrpc": "2.0", "id": i, "method": "resources/read", "params": {"uri": tool["_meta"]["ui"]["resourceUri"]}})
    result = subprocess.run([sys.executable, "-I", "-S", str(folder / "server/nacos-registry.pyz"), "--state-dir", str(folder / "state"), "serve"], input="\n".join(map(json.dumps, calls)) + "\n", cwd=folder, env=env, check=True, capture_output=True, text=True)
    for tool, line in zip(ui_tools, result.stdout.splitlines()[-2:]):
        page = json.loads(line)["result"]["contents"][0]
        assert page["mimeType"] == "text/html;profile=mcp-app" and "Nacos 资源中心" in page["text"]
        assert page["uri"] == tool["_meta"]["ui"]["resourceUri"]
        assert '"entrypoint": "' + tool["_meta"]["openai/ui"]["entrypoints"][0]["type"] + '"' in page["text"]
    runtime = (folder / "server/nacos-registry.pyz").read_bytes()
    source_hash = json.loads((folder / "build-info.json").read_text())["sourceTreeSha256"]
    # Reproduce an installer removing an old bundle while its MCP process is
    # still attached to a conversation. First opening either page must survive.
    old_bundle = folder / "previous-runtime.pyz"
    old_bundle.write_bytes(runtime)
    process = subprocess.Popen(
        [sys.executable, "-I", "-S", str(old_bundle), "--state-dir", str(folder / "state"), "serve"],
        cwd=folder, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    watchdog = threading.Timer(20, process.kill)
    watchdog.start()
    try:
        process.stdin.write("\n".join(map(json.dumps, calls[:2])) + "\n")
        process.stdin.flush()
        assert json.loads(process.stdout.readline())["result"]["serverInfo"]["version"] == version
        live_tools = json.loads(process.stdout.readline())["result"]["tools"]
        assert {t["name"] for t in ui_tools} <= {t["name"] for t in live_tools}
        old_bundle.unlink()
        reads = calls[2:] + [{"jsonrpc": "2.0", "id": 99, "method": "ping"}]
        output, errors = process.communicate("\n".join(map(json.dumps, reads)) + "\n", timeout=15)
        assert process.returncode == 0, errors
        replies = [json.loads(line) for line in output.splitlines()]
        assert len(replies) == 3
        for tool, reply in zip(ui_tools, replies[:2]):
            page = reply["result"]["contents"][0]
            assert page["uri"] == tool["_meta"]["ui"]["resourceUri"]
            assert '"entrypoint": "' + tool["_meta"]["openai/ui"]["entrypoints"][0]["type"] + '"' in page["text"]
        assert replies[-1]["result"] == {}
    finally:
        watchdog.cancel()
        if process.poll() is None:
            process.kill()
            process.wait()

source_archive = ROOT / "dist" / f"nacos-ai-registry-{version}-source.zip"
assert hashlib.sha256(source_archive.read_bytes()).hexdigest() == source_archive.with_suffix(".zip.sha256").read_text().split()[0]
with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder).resolve()
    with zipfile.ZipFile(source_archive) as archive:
        for name in archive.namelist():
            assert not name.startswith("/") and ".." not in Path(name).parts
        archive.extractall(folder)
    assert (folder / "codex/plugin.json").is_file()
    assert (folder / "specs/functional-spec.md").is_file()
    check_document_links(folder)
    subprocess.run([sys.executable, "scripts/build.py"], cwd=folder / "codex", env=env, check=True, capture_output=True, text=True)
    rebuilt = folder / "codex/dist/nacos-ai-registry"
    assert (rebuilt / "server/nacos-registry.pyz").read_bytes() == runtime
    assert json.loads((rebuilt / "build-info.json").read_text())["sourceTreeSha256"] == source_hash
print("PASS: archives, manifests, checksums, documentation links, isolated source rebuild, clean CLI and stdio MCP, live pages after bundle removal")
