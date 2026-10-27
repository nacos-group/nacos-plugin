# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Local reuse preferences and non-installing access to validated Skill contents."""
from . import package
from .errors import require

INSTALL_POLICIES = ("ask", "auto", "never")


class DiscoveryMixin:
    def discovery_settings(self):
        # Separate from the connection fingerprint: changing a preference must not
        # orphan existing installations, credentials, tasks, or connection records.
        policy = self.data.get("discovery", {}).get("installPolicy", "ask")
        require(policy in INSTALL_POLICIES, "Unknown discovery installation policy", "configuration")
        return {"installPolicy": policy, "scope": "implicit_discovery",
                "installTiming": "after_successful_use", "explicitRequests": "independent"}

    def configure_discovery(self, installPolicy):
        require(installPolicy in INSTALL_POLICIES, "Invalid discovery installation policy")
        self.data["discovery"] = {"installPolicy": installPolicy}
        self.store.save()
        return self.discovery_settings()

    def check_discovery_reuse(self, mode):
        # The caller supplies the workflow origin and successful-use decision.
        # This guard enforces the stored policy, not proof of model reasoning or
        # user consent. Explicit management retains its ordinary authorization.
        if mode is None:
            return
        require(mode in ("automatic", "confirmed"), "Invalid discovery reuse mode")
        policy = self.discovery_settings()["installPolicy"]
        require(policy != "never", "Discovery installation disabled; explicit management is separate", "permission")
        require(mode != "automatic" or policy == "auto", "Discovery installation requires the user's choice", "permission")

    def preview_skill(self, name, version=None, label=None, file="SKILL.md"):
        resolved, md5, data = self.registry().download(name, version, label)
        files = package.unpack(data)
        require(package.metadata(files["SKILL.md"])["name"] == name, "Resource identity differs from package Skill name", "conflict")
        package.path_name(file)
        require(file in files, "Selected file is not in this Skill package", "not_found")
        require(len(files[file]) <= 256 * 1024, "Selected text file exceeds preview limit")
        try:
            text = files[file].decode("utf-8")
        except UnicodeError:
            require(False, "Selected file is not UTF-8 text")
        return {"ref": self.reference("skill", name), "version": resolved, "serverMd5": md5,
                "file": file, "content": text, "files": sorted(files), "installed": False,
                "contentTrust": "untrusted_resource", "execution": "not_performed"}
