# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
import argparse
import json
import sys

from nacos_registry.errors import PluginError
from nacos_registry.schema import validate
from nacos_registry.store import Store

from . import __version__
from .server import DEFINITIONS, serve
from .service import Service


def main():
    parser = argparse.ArgumentParser(description="Nacos AI Registry for local Qoder")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--state-dir", help="Private Qoder plugin state directory")
    parser.add_argument("action", choices=["serve", *DEFINITIONS], nargs="?", default="serve")
    parser.add_argument("--input", help="Nonsecret JSON argument file, or - for stdin")
    args = parser.parse_args()
    try:
        service = Service(Store(args.state_dir)) if args.state_dir else Service()
        if args.action == "serve":
            serve(service)
            return
        if args.input == "-":
            value = json.load(sys.stdin)
        elif args.input:
            with open(args.input) as stream:
                value = json.load(stream)
        else:
            value = {}
        validate(value, DEFINITIONS[args.action][1])
        context = value.pop("_context", None)
        result = service.invoke(args.action, value, expected_context=context)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if isinstance(result, dict) and result.get("status") in ("failed", "result_unknown", "recovery_required"):
            sys.exit(1)
    except PluginError as exc:
        print(json.dumps(exc.result()), file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError, TypeError, KeyError):
        print('{"error":"local_failure","message":"Input or local state could not be processed"}', file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
