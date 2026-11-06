#!/usr/bin/env python3
# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Deterministic external scanner fixture; exercises Nacos' real review pipeline."""
from pathlib import Path
import sys

if "--version" in sys.argv:
    print("agent-plugin-integration-scanner 1.0")
    sys.exit(0)
roots = [Path(arg) for arg in sys.argv[1:] if Path(arg).is_dir()]
if not roots:
    sys.exit("Expected a scanner input directory")
rejected = any(b"IT_REJECT" in path.read_bytes()
               for root in roots for path in root.rglob("*") if path.is_file())
print("Synthetic review: rejected" if rejected else "Synthetic review: approved")
sys.exit(1 if rejected else 0)
