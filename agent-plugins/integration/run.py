#!/usr/bin/env python3
# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Launch an owned, temporary Nacos process and test both adapters over real HTTP."""
import argparse
import base64
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib import error, parse, request

ROOT = Path(__file__).resolve().parent
ADAPTERS = ROOT.parent


def ports():
    # Also reserve Nacos' main-port-relative gRPC/raft ports while selecting.
    for _ in range(100):
        base = 18000 + secrets.randbelow(25000)
        chosen = [base, base + 1000, base + 1001, base - 1000, base + 2, base + 3]
        sockets = []
        try:
            for port in chosen:
                sock = socket.socket()
                sockets.append(sock)
                sock.bind(("127.0.0.1", port))
            return base, base + 2, base + 3
        except OSError:
            pass
        finally:
            for sock in sockets:
                sock.close()
    raise RuntimeError("Cannot allocate test server ports")


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nacos-home", type=Path, required=True, help="Extracted fixed-revision Nacos distribution")
    parser.add_argument("--adapter", choices=["codex", "qoder", "all"], default="all")
    parser.add_argument("--auth", choices=["enabled", "disabled"], default="enabled")
    parser.add_argument("--output", type=Path, required=True, help="Reports outside source/package directories")
    args = parser.parse_args()
    jar = args.nacos_home.resolve() / "target/nacos-server.jar"
    if not jar.is_file():
        parser.error("nacos-home must contain target/nacos-server.jar")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    failed = False
    with tempfile.TemporaryDirectory(prefix="nacos-agent-it-") as temp:
        runtime = Path(temp)
        home = runtime / "nacos"
        shutil.copytree(args.nacos_home / "conf", home / "conf")
        (home / "logs").mkdir()
        scanner = runtime / "scanner"
        scanner.write_text("#!" + sys.executable + "\n" + "\n".join((ROOT / "scanner.py").read_text().splitlines()[1:]) + "\n")
        scanner.chmod(0o700)
        main_port, console_port, registry_port = ports()
        enabled = str(args.auth == "enabled").lower()
        password = secrets.token_urlsafe(24)
        jwt_secret = base64.b64encode(secrets.token_bytes(48)).decode()
        identity = secrets.token_hex(20)
        config = {
            "nacos.server.main.port": main_port, "nacos.console.port": console_port,
            "nacos.ai.registry.port": registry_port, "server.address": "127.0.0.1",
            "nacos.inetutils.ip-address": "127.0.0.1",
            "nacos.core.auth.enabled": enabled, "nacos.core.auth.admin.enabled": enabled,
            "nacos.core.auth.console.enabled": enabled,
            "nacos.core.auth.server.identity.key": "agent-it-identity",
            "nacos.core.auth.server.identity.value": identity,
            "nacos.plugin.auth.nacos.token.secret.key": jwt_secret,
            "nacos.plugin.auth.nacos.caching.enabled": "false",
            "nacos.plugin.ai-pipeline.enabled": "true",
            "nacos.plugin.ai-pipeline.type": "skill-scanner",
            "nacos.plugin.ai-pipeline.skill-scanner.command": scanner,
            "nacos.plugin.ai-pipeline.skill-scanner.use-llm": "false",
            "nacos.ai.skill.auto-publish-after-review.enabled": "false",
        }
        with (home / "conf/application.properties").open("a") as file:
            file.write("\n# Disposable agent-plugin integration environment\n")
            file.writelines(f"{key}={value}\n" for key, value in config.items())
        url = f"http://127.0.0.1:{main_port}/nacos"
        metadata = {"requestedNacosRevision": (ROOT / "nacos-ref.txt").read_text().strip(),
                    "ciSourceRevision": os.environ.get("NACOS_IT_SOURCE_REVISION"),
                    "auth": args.auth, "python": sys.version.split()[0], "adapters": {}}
        command = ["java", "-Xms256m", "-Xmx1024m", "-Dnacos.standalone=true",
                   "-Dnacos.deployment.type=merged", "-Dnacos.home=" + str(home),
                   "--add-opens=java.base/java.lang=ALL-UNNAMED",
                   "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED",
                   "--add-opens=java.base/java.util=ALL-UNNAMED",
                   "-jar", str(jar),
                   "--spring.config.additional-location=file:" + str(home / "conf") + "/",
                   "--logging.config=" + str(home / "conf/nacos-logback.xml")]
        startup = runtime / "startup.log"
        with startup.open("wb") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 180
            while True:
                if process.poll() is not None:
                    raise RuntimeError("Nacos exited during startup; inspect startup.log")
                try:
                    with request.urlopen(url + "/v3/admin/core/state", timeout=2):
                        break
                except error.HTTPError as exc:
                    if exc.code in (401, 403):
                        break
                except (error.URLError, TimeoutError):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError("Nacos readiness timed out")
                time.sleep(1)
            if args.auth == "enabled":
                data = parse.urlencode({"password": password}).encode()
                with request.urlopen(request.Request(url + "/v3/auth/user/admin", data=data), timeout=20) as response:
                    result = json.load(response)
                if result.get("code") != 0:
                    raise RuntimeError("Temporary admin initialization failed")
            selected = ["codex", "qoder"] if args.adapter == "all" else [args.adapter]
            for adapter in selected:
                # Separate interpreters prevent the adapters' identically named modules sharing imports.
                env = dict(os.environ, PYTHONPATH=str(ADAPTERS / adapter / "src"),
                           NACOS_IT_URL=url, NACOS_IT_ADAPTER=adapter, NACOS_IT_AUTH=args.auth,
                           NACOS_IT_USER="nacos", NACOS_IT_PASSWORD=password,
                           NACOS_IT_ROOT=str(runtime / adapter),
                           NACOS_IT_REPORT=str(output / f"{adapter}.json"),
                           NACOS_IT_DOWNSTREAM_TOKEN=secrets.token_urlsafe(20))
                with (output / f"{adapter}.log").open("wb") as log:
                    completed = subprocess.run([sys.executable, "-u", str(ROOT / "test_registry.py")],
                                               env=env, stdout=log, stderr=subprocess.STDOUT, timeout=600)
                metadata["adapters"][adapter] = {"exitCode": completed.returncode}
                print(f"{adapter} ({args.auth}): {'PASS' if completed.returncode == 0 else 'FAIL'}", flush=True)
                failed |= completed.returncode != 0
        finally:
            stop(process)
            # Only generated credentials exist here; redact them even in disposable diagnostic artifacts.
            text = startup.read_text(errors="replace")
            for secret in (password, jwt_secret, identity):
                text = text.replace(secret, "[redacted]")
            (output / "startup.log").write_text(text)
            (output / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
