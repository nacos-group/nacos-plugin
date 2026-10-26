# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Typed, content-free diagnostics; never propagate raw HTTP bodies or secrets."""
class PluginError(Exception):
    def __init__(self, kind, message, **details):
        super().__init__(message)
        self.kind, self.message, self.details = kind, message, details

    def result(self):
        return {"error": self.kind, "message": self.message, **self.details}


def require(condition, message, kind="validation"):
    if not condition:
        raise PluginError(kind, message)
