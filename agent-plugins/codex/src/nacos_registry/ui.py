# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Assemble shared offline UI modules with an explicit MCP entrypoint."""
import json
from importlib.resources import files
from . import __version__


def render_ui(entrypoint="global"):
    if entrypoint not in ("global", "thread"):
        raise ValueError("Unknown UI entrypoint")
    root = files("nacos_registry").joinpath("ui")
    html = root.joinpath("center.html").read_text(encoding="utf-8")
    css = root.joinpath("theme.css").read_text(encoding="utf-8")
    scripts = "\n".join(root.joinpath(name + ".js").read_text(encoding="utf-8")
                        for name in ("model", "bridge", "components", "settings-model", "settings", "app"))
    scripts = "globalThis.NacosBuild = " + json.dumps({"version": __version__, "entrypoint": entrypoint}) + ";\n" + scripts
    return html.replace("/* APP_STYLE */", css).replace("/* APP_SCRIPT */", scripts)
