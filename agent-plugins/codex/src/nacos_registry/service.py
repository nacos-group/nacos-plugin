# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Shared application core. Tool and CLI entrypoints use these same local facts."""
import copy
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time

from .errors import PluginError, require
from .credentials import Keychain, reference as credential_reference
from .credential_service import CredentialMixin, references
from .hosts.codex import local_defaults
from . import package
from .registry import Registry
from .remote import RemoteMixin
from .store import Store, atomic_write, digest, new_id, safe_path
from .transport import checked_url

SCOPES = {"read", "develop", "publish", "install", "call"}


def governance(meta):
    if meta is None:
        return None
    return {k: v for k, v in meta.items() if k not in ("downloadCount", "updateTime", "versions")} | {
        "versions": [{k: v for k, v in x.items() if k not in ("downloadCount",)} for x in meta.get("versions", [])]}


def semantic(files):
    """The server normalizes frontmatter version/formatting; compare content semantics."""
    value = dict(files)
    md = value.pop("SKILL.md").decode()
    match = re.match(r"\A---\r?\n.*?\r?\n---(?:\r?\n|$)", md, re.S)
    meta = package.metadata(files["SKILL.md"])
    meta.pop("version", None)
    return {"files": package.hashes(value), "metadata": meta, "body": md[match.end():].strip()}


def review_summary(value):
    if not value:
        return None
    try:
        value = json.loads(value) if isinstance(value, str) else value
        return {"status": value.get("status", "unknown"), "checks": [{"nodeId": x.get("nodeId"), "passed": x.get("passed")} for x in value.get("pipeline", [])]}
    except (ValueError, TypeError, AttributeError):
        return {"status": "unknown"}


def file_changes(before, after):
    before, after = before or {}, after or {}
    return {"added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after)),
            "modified": sorted(x for x in before.keys() & after.keys() if before[x] != after[x])}


class Service(RemoteMixin, CredentialMixin):
    def __init__(self, store=None, registry_factory=Registry, vault=None):
        self.store = store or Store()
        self.registry_factory = registry_factory
        self.vault = vault or Keychain(self.store.root)

    def invoke(self, action, arguments=None, expected_context=None):
        require(action in ACTIONS, "Unknown action", "unsupported")
        with self.store.locked():
            if expected_context is not None:
                require(expected_context == digest(self.data["profile"]), "Connection changed; refresh the page before continuing", "conflict")
            return getattr(self, action)(**(arguments or {}))

    @property
    def data(self):
        return self.store.data

    def profile(self, scope="read"):
        p = self.data["profile"]
        require(p is not None, "Run setup to configure a registry", "configuration")
        require(scope in p["allowedOperations"], "Operation disabled by local configuration", "permission")
        return p

    def registry(self, scope="read"):
        p = self.profile(scope)
        return Registry(p, self.resolve_credentials) if self.registry_factory is Registry else self.registry_factory(p)

    def reference(self, resource_type, name):
        p = self.profile()
        require(isinstance(name, str) and 0 < len(name) <= 128, "Invalid resource name")
        return {"registryId": p["id"], "namespaceId": p["namespaceId"], "resourceType": resource_type, "name": name}

    def key(self, ref):
        return digest(ref)

    def configure(self, profile):
        p = self.validate_profile(profile)
        self.validate_references(p)
        return self.persist_profile(p)

    def validate_profile(self, profile):
        require(isinstance(profile, dict), "Profile must be an object")
        allowed = {"id", "displayName", "identityId", "namespaceId", "clientUrl", "adminUrl", "clientAuth", "adminAuth", "allowedOperations", "scanRoots", "installRoots", "codexConfig"}
        require(set(profile) <= allowed, "Profile has unknown fields; use credential references only")
        p = copy.deepcopy(profile)
        for field in ("id", "identityId", "namespaceId"):
            require(isinstance(p.get(field), str) and p[field].strip(), "Profile requires id, identityId and namespaceId")
        for field in ("clientUrl", "adminUrl"):
            p[field] = checked_url(p[field])
        require(set(p.get("allowedOperations", [])) <= SCOPES and "read" in p["allowedOperations"], "Invalid operation scope")
        for field in ("clientAuth", "adminAuth"):
            auth = p.setdefault(field, {"type": "none"})
            kind = auth.get("type")
            if auth.get("source") == "local":
                require(kind in ("login", "token") and set(auth) <= {"type", "source", "credentialRef"}, "Invalid local credential reference")
                if "credentialRef" in auth: credential_reference(auth["credentialRef"])
                continue
            keys = {"none": {"type"}, "token": {"type", "tokenEnv"}, "login": {"type", "usernameEnv", "passwordEnv"}}.get(kind)
            require(keys is not None and set(auth) == keys, "Invalid registry auth references")
            for key in keys - {"type"}:
                require(re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", auth[key]) is not None, "Invalid credential environment reference")
        for field in ("scanRoots", "installRoots"):
            require(isinstance(p.get(field, []), list) and len(p.get(field, [])) <= 16, "At most 16 explicit roots")
            p[field] = [str(self.allowed_root(x)) for x in p.get(field, [])]
        if p.get("codexConfig"):
            config = safe_path(p["codexConfig"])
            require(config.name == "config.toml", "Expected Codex config.toml")
            p["codexConfig"] = str(config)
        return p

    def persist_profile(self, p, created=()):
        self.validate_references(p, created)
        previous = self.data["profile"]
        if previous and digest(previous) != digest(p):
            # Keep history and installations; invalidate plans/scan selections on context changes.
            # Retain old plans for recovery; context fingerprints prevent their use here.
            self.data["onboarding"] = {"status": "not_started"}
        self.data["profile"] = p
        garbage = set(self.data.get("credentialGarbage", [])) | (references(previous) - references(p))
        self.data["credentialGarbage"] = sorted(garbage - references(p))
        self.store.save()
        pending = self.cleanup_credentials()
        return {"status": "configured", "connection": "unverified", "profile": p, "credentialCleanupPending": pending}

    def allowed_root(self, value):
        p = safe_path(value)
        require(p != Path(p.anchor) and p != Path.home(), "Choose a specific Skill directory")
        require(not any(x in p.parts for x in (".system", "cache", "node_modules", ".git")), "System/cache directories cannot be managed")
        own = Path(__file__).resolve().parent
        require(p != own and own not in p.parents and p not in own.parents, "Plugin source cannot be managed")
        return p

    def status(self):
        p = self.data["profile"]
        current = lambda x: p and x.get("context") == digest(p)
        scan = self.data["scans"].get(self.data["onboarding"].get("scanId"))
        return {"profile": p, "context": digest(p), "defaults": local_defaults(self.allowed_root), "onboarding": self.data["onboarding"],
                "credentialStorage": self.vault.capabilities(), "credentials": self.credential_status(),
                "credentialCleanupPending": bool(self.data.get("credentialGarbage")),
                "scan": scan if scan and current(scan) else None,
                "installations": [x for x in self.data["installations"].values() if current(x)],
                "bindings": [x for x in self.data["bindings"].values() if current(x)],
                "connections": [x for x in self.data["connections"].values() if current(x)],
                "tasks": [{"taskHandle": x["id"], "ref": x["connection"]["ref"], "connectionId": x["connection"]["id"],
                           "status": x.get("status", "unknown"), "updatedAt": x.get("updatedAt"),
                           "cancelRequested": x.get("cancelRequested", False)}
                          for x in self.data["tasks"].values() if current(x)],
                "unfinishedOperations": [x for x in self.data["operations"].values()
                                         if x["status"] in ("running", "result_unknown", "recovery_required") and self.operation_current(x)]}

    def operation_current(self, operation):
        context = operation.get("context") or self.data["plans"].get(operation.get("planId"), {}).get("context")
        return bool(self.data["profile"] and context == digest(self.data["profile"]))

    def diagnose(self):
        r = self.registry()
        result = r.search(query="", limit=1)
        return {"clientRead": "passed", "adminWrite": "not_probed", "resourceCount": len(result.get("items", [])), "checkedAt": time.time()}

    def search(self, **kwargs):
        return {"source": self.reference("search", "*"), "authoritative": False, "result": self.registry().search(**kwargs)}

    def my_skills(self, query="", page=1, limit=20):
        return self.registry("develop").my_skills(query, page, limit)

    def scan(self, roots=None):
        p = self.profile()
        roots = roots if roots is not None else p["scanRoots"]
        require(isinstance(roots, list) and len(roots) <= 16, "Invalid scan roots")
        chosen = [str(safe_path(x)) for x in roots]
        require(all(x in p["scanRoots"] for x in chosen), "Scan root not configured", "permission")
        scan_id, items = new_id(), []
        for root in chosen:
            try:
                path = self.allowed_root(root)
                require(path.is_dir(), "Scan root unavailable")
                if (path / "SKILL.md").is_file():
                    candidates = [path]
                else:
                    candidates = []
                    for entry in path.iterdir():
                        require(len(candidates) < 500, "Scan root has too many entries")
                        candidates.append(entry)
                for item in sorted(candidates):
                    if item.name.startswith("."):
                        continue
                    candidate = {"id": new_id(), "path": str(item), "root": root, "source": "user-selected", "status": "skipped"}
                    try:
                        self.allowed_root(item)
                        if not item.is_dir() or not (item/"SKILL.md").exists():
                            continue
                        md = safe_path(item / "SKILL.md")
                        require(md.stat().st_size <= 1024 * 1024, "SKILL.md exceeds limit")
                        meta = package.metadata(md.read_bytes())
                        candidate.update(name=meta["name"], description=meta["description"], status="candidate")
                        # Listing metadata only: no package precheck/upload, no content digest here.
                        candidate["binding"] = next((x["id"] for x in self.data["bindings"].values() if x["path"] == str(item) and x["context"] == digest(p)), None)
                    except (PluginError, OSError, UnicodeError) as exc:
                        candidate.update(status="unreadable", reason=exc.kind if isinstance(exc, PluginError) else "filesystem")
                    items.append(candidate)
            except (PluginError, OSError) as exc:
                items.append({"root": root, "status": "failed", "reason": exc.kind if isinstance(exc, PluginError) else "filesystem"})
        record = {"id": scan_id, "context": digest(p), "roots": chosen, "items": items}
        self.data["scans"][scan_id] = record
        self.data["onboarding"] = {"status": "awaiting_selection", "scanId": scan_id}
        self.store.save()
        return record

    def onboarding(self, action):
        require(action in ("skip", "finish", "reopen"), "Invalid onboarding action")
        self.data["onboarding"]["status"] = {"skip": "skipped", "finish": "complete", "reopen": "awaiting_scan"}[action]
        self.store.save()
        return self.data["onboarding"]

    def candidate(self, scanId, candidateId):
        scan = self.data["scans"].get(scanId)
        require(scan and scan["context"] == digest(self.profile()), "Scan is stale", "conflict")
        item = next((x for x in scan["items"] if x.get("id") == candidateId), None)
        require(item and item["status"] == "candidate", "Candidate unavailable")
        self.allowed_root(item["path"])
        return item

    def select(self, scanId, selections):
        require(isinstance(selections, list) and len(selections) <= 500, "Invalid selections")
        results = []
        for choice in selections:
            try:
                item = self.candidate(scanId, choice["candidateId"])
                action = choice["action"]
                require(action in ("ignore", "track"), "Use upload_plan for content transfer")
                key = digest({"path": item["path"], "context": digest(self.profile())})
                existing = self.data["bindings"].get(key, {})
                binding = {**existing, "id": key, "path": item["path"], "context": digest(self.profile()), "policy": action}
                self.data["bindings"][key] = binding
                results.append({"candidateId": item["id"], "status": action, "bindingId": key})
            except PluginError as exc:
                results.append({"candidateId": choice.get("candidateId"), **exc.result()})
        self.store.save()
        return {"results": results}

    def plan(self, kind, ref, **fields):
        identifier = new_id()
        value = {"id": identifier, "kind": kind, "ref": ref, "context": digest(self.profile()), "createdAt": time.time(), "status": "planned", **fields}
        self.data["plans"][identifier] = value
        self.store.save()
        return value

    def snapshot(self, files):
        identifier = new_id()
        atomic_write(self.store.artifact(identifier), package.pack(files))
        return identifier

    def meta_or_none(self, registry, name):
        try:
            return registry.skill_meta(name)
        except PluginError as exc:
            if exc.kind == "not_found": return None
            raise

    def upload_plan(self, scanId, candidateId, overwriteDraft=False, bindExisting=False, commitMessage="", expectedContentHash=None):
        r = self.registry("develop")
        item = self.candidate(scanId, candidateId)
        files = package.read_directory(item["path"])
        if expectedContentHash is not None:
            require(expectedContentHash == digest(package.hashes(files)), "Selected files changed; review the upload preview again", "conflict")
        name = package.metadata(files["SKILL.md"])["name"]
        ref = self.reference("skill", name)
        binding_key = digest({"path": item["path"], "context": digest(self.profile())})
        binding = self.data["bindings"].get(binding_key, {})
        before = self.meta_or_none(r, name)
        if before is not None and binding.get("ref") != ref and not bindExisting:
            raise PluginError("conflict", "Existing remote resource requires explicit binding; same name is insufficient",
                              conflict={"type": "upload_binding", "name": name, "namespaceId": ref["namespaceId"],
                                        "requiresBind": True, "draftVersion": before.get("editingVersion")})
        if binding.get("remoteVersion"):
            latest = ((before or {}).get("labels") or {}).get("latest")
            require(not latest or latest in (binding["remoteVersion"], binding.get("basePublishedVersion")), "Remote published version advanced since binding; reconcile both sides", "conflict")
            remote = package.hashes(package.unpack(r.draft_zip(name, binding["remoteVersion"])))
            require(remote == binding["remoteHashes"], "Remote content changed since binding; reconcile both sides", "conflict")
        zipped = package.pack(files)
        checks = r.precheck(zipped)
        require(isinstance(checks, list) and len(checks) == 1 and isinstance(checks[0], dict) and checks[0].get("skillName") == name, "Precheck did not identify the selected Skill", "protocol")
        check = checks[0]
        code = check.get("precheckCode")
        require(code in ("READY", "VERSION_ADJUSTED", "DRAFT_EXISTS"), "Upload precheck blocked the operation", code or "protocol")
        if code == "DRAFT_EXISTS" and not overwriteDraft:
            raise PluginError("conflict", "Existing draft needs explicit overwrite selection",
                              conflict={"type": "upload_draft", "name": name, "namespaceId": ref["namespaceId"],
                                        "requiresOverwrite": True, "draftVersion": check.get("editingVersion")})
        editing = check.get("editingVersion")
        baseline = package.hashes(package.unpack(r.draft_zip(name, editing))) if editing else None
        return self.plan("upload", ref, snapshot=self.snapshot(files), localPath=item["path"], localHashes=package.hashes(files),
                         remoteBaseline=governance(before), draftVersion=editing, draftHashes=baseline,
                         precheck=check, action="OVERWRITE_DRAFT" if code == "DRAFT_EXISTS" else "CREATE_DRAFT",
                         targetVersion=editing if code == "DRAFT_EXISTS" else check.get("targetVersion"),
                         changes=file_changes(baseline, package.hashes(files)),
                         bindingId=binding_key, commitMessage=commitMessage, effects=["upload draft", "does not submit or publish"],
                         visibility=before.get("scope", "server_default_unknown") if before else "server_default_unknown")

    def upload_preview(self, scanId, candidateId):
        self.profile("develop")
        item = self.candidate(scanId, candidateId)
        content = package.read_directory(item["path"])
        return {"name": item["name"], "path": item["path"], "destination": self.profile()["adminUrl"],
                "namespaceId": self.profile()["namespaceId"], "files": [{"path": name, "bytes": len(data)} for name, data in sorted(content.items())],
                "contentHash": digest(package.hashes(content))}

    def install_plan(self, name, installRoot, version=None, label=None):
        r = self.registry("install")
        root = str(safe_path(installRoot))
        require(root in self.profile()["installRoots"], "Installation root not configured", "permission")
        resolved, md5, data = r.download(name, version, label)
        files = package.unpack(data)
        require(package.metadata(files["SKILL.md"])["name"] == name, "Resource identity differs from package Skill name", "conflict")
        target = self.allowed_root(Path(root) / name)
        ref = self.reference("skill", name)
        key = digest({"ref": ref, "path": str(target)})
        old = self.data["installations"].get(key)
        current = package.disk_hashes(target)
        require(not old or old.get("context") == digest(self.profile()), "Installation belongs to a different connection context", "conflict")
        if current is not None and not (old and old["hashes"] == current):
            raise PluginError("conflict", "Target exists or has local modifications; preserve and reconcile it",
                              conflict={"type": "local_files", "target": str(target), "owned": bool(old),
                                        "changes": file_changes(old.get("hashes") if old else {}, current)})
        return self.plan("install", ref, installationId=key, target=str(target), localBaseline=current,
                         snapshot=self.snapshot(files), hashes=package.hashes(files), version=resolved, serverMd5=md5,
                         selector={"version": version, "label": label}, previous=copy.deepcopy(old),
                         changes=file_changes(current, package.hashes(files)),
                         loadState="pending_host_verification")

    def skill_status(self, name, version=None):
        r = self.registry("develop")
        meta = r.skill_meta(name)
        result = {"ref": self.reference("skill", name), "metadata": meta}
        if version:
            content = package.unpack(r.draft_zip(name, version))
            result.update(version=version, hashes=package.hashes(content))
        return result

    def publish_plan(self, name, version, action):
        r = self.registry("publish")
        require(action in ("submit", "publish"), "Choose submit or publish")
        meta = r.skill_meta(name)
        selected = next((x for x in meta.get("versions", []) if x["version"] == version), None)
        require(selected, "Version not found", "not_found")
        if action == "publish":
            require(selected["status"] == "reviewed", "Publish requires a completed review", "conflict")
            review = review_summary(selected.get("publishPipelineInfo")) or {}
            require(review.get("status") == "APPROVED", "Review is rejected or approval cannot be verified", "review_rejected" if review.get("status") in ("REJECTED", "FAILED") else "review_unverified")
        require(meta.get("scope") in ("PUBLIC", "PRIVATE", "public", "private"), "Cannot verify target visibility; inspect server metadata", "unsupported")
        return self.plan(action, self.reference("skill", name), version=version, remoteBaseline=governance(meta),
                         visibility=meta["scope"], currentStatus=selected["status"],
                         effects=["May become online immediately without a matching pipeline" if action == "submit" else "Publish only after server review checks"])

    def apply(self, planId):
        p = self.data["plans"].get(planId)
        require(p is not None, "Plan not found", "not_found")
        require(p["context"] == digest(self.profile()), "Profile changed; plan is stale", "conflict")
        if p["status"] == "completed":
            return self.data["operations"][p["operationId"]]
        require(p["status"] == "planned", "Operation already started; inspect or recover it before retry", "conflict")
        require(time.time() - p["createdAt"] < 3600, "Plan expired; create a fresh plan", "conflict")
        kind = p["kind"]
        scopes = {"upload": "develop", "submit": "publish", "publish": "publish", "install": "install", "uninstall": "install", "restore": "install", "mcp_config": "install", "bind_agent": "call", "disconnect": "install"}
        self.profile(scopes[kind])
        operation = self.store.operation(kind, p["ref"])
        operation["planId"] = planId
        p.update(status="started", operationId=operation["id"])
        self.store.save()
        try:
            result = getattr(self, "apply_" + kind)(p, operation)
            operation.update(status="completed", result=result)
            p["status"] = "completed"
        except PluginError as exc:
            operation.update(status="result_unknown" if exc.kind == "result_unknown" else "recovery_required" if operation.get("backup") or operation.get("configBackup") else "failed", error=exc.result())
        except Exception:
            operation.update(status="recovery_required" if operation.get("backup") or operation.get("configBackup") else "result_unknown", error={"error": "internal", "message": "Inspect the operation; raw diagnostic omitted"})
        self.store.save()
        return operation

    def apply_upload(self, p, operation):
        r = self.registry("develop")
        name = p["ref"]["name"]
        require(package.hashes(package.read_directory(p["localPath"])) == p["localHashes"], "Local upload content changed", "conflict")
        require(governance(self.meta_or_none(r, name)) == p["remoteBaseline"], "Remote state changed since upload plan", "conflict")
        if p["draftVersion"]:
            require(package.hashes(package.unpack(r.draft_zip(name, p["draftVersion"]))) == p["draftHashes"], "Draft content changed", "conflict")
        data = self.store.artifact(p["snapshot"]).read_bytes()
        require(package.hashes(package.unpack(data)) == p["localHashes"], "Upload snapshot changed", "conflict")
        require(bool(p["targetVersion"]), "Precheck did not resolve a target version", "protocol")
        returned = r.upload(data, p["action"], p["targetVersion"], p["commitMessage"])
        require(returned == name, "Upload returned an unexpected resource; reconcile manually", "result_unknown")
        try:
            meta = r.skill_meta(name)
            version = meta.get("editingVersion")
            require(bool(version), "Upload completed but draft version cannot be verified", "result_unknown")
            remote = package.unpack(r.draft_zip(name, version))
            require(semantic(remote) == semantic(package.unpack(data)), "Uploaded draft differs from planned content", "result_unknown")
        except PluginError as exc:
            raise PluginError("result_unknown", "Upload sent; verify exact draft before retry", cause=exc.kind) from None
        self.data["bindings"][p["bindingId"]] = {"id": p["bindingId"], "path": p["localPath"], "context": p["context"],
              "ref": p["ref"], "policy": "explicit", "localHashes": p["localHashes"], "remoteVersion": version, "remoteHashes": package.hashes(remote), "basePublishedVersion": ((p["remoteBaseline"] or {}).get("labels") or {}).get("latest")}
        return {"ref": p["ref"], "version": version, "status": "draft", "visibility": meta.get("scope", "unknown"), "consumerVerified": False}

    def apply_submit(self, p, operation):
        return self.apply_lifecycle(p)

    def apply_publish(self, p, operation):
        return self.apply_lifecycle(p)

    def apply_lifecycle(self, p):
        r = self.registry("publish")
        name = p["ref"]["name"]
        require(governance(r.skill_meta(name)) == p["remoteBaseline"], "Version or visibility changed since plan", "conflict")
        r.lifecycle(name, p["version"], p["kind"])
        try:
            meta = r.skill_meta(name)
            version = next((x for x in meta.get("versions", []) if x["version"] == p["version"]), None)
            require(version, "Cannot verify submitted version", "result_unknown")
        except PluginError:
            raise PluginError("result_unknown", "Lifecycle request sent; exact version state is unverified") from None
        result = {"ref": p["ref"], "version": p["version"], "status": version["status"], "visibility": meta.get("scope"), "consumerVerified": False,
                  "review": review_summary(version.get("publishPipelineInfo"))}
        if str(version["status"]).lower() == "online":
            try:
                resolved, _, data = r.download(name, p["version"])
                package.unpack(data)
                result.update(consumerVerified=True, resolvedVersion=resolved)
            except PluginError as exc:
                result["consumerError"] = exc.result()
        return result

    def replace_directory(self, target, files, operation, previous):
        target = safe_path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        backup = self.snapshot(package.read_directory(target)) if target.exists() else None
        operation.update(backup=backup, target=str(target), previous=previous,
                         beforeHashes=package.disk_hashes(target), afterHashes=package.hashes(files))
        self.store.save()
        # Stage beside the destination so rename stays on the same filesystem.
        staging = Path(tempfile.mkdtemp(prefix=".nacos-stage-", dir=target.parent))
        displaced = target.parent / (".nacos-old-" + operation["id"])
        operation.update(staging=str(staging), displaced=str(displaced))
        self.store.save()
        try:
            for name, content in files.items():
                atomic_write(staging / name, content)
            require(package.disk_hashes(target) == operation["beforeHashes"], "Target changed during staging", "conflict")
            if target.exists():
                os.rename(target, displaced)
            os.rename(staging, target)
            operation["filesApplied"] = True
            self.store.save()
            if displaced.exists():
                shutil.rmtree(displaced)
        finally:
            if staging.exists():
                shutil.rmtree(staging)

    def apply_install(self, p, operation):
        require(package.disk_hashes(p["target"]) == p["localBaseline"], "Installation target changed", "conflict")
        # Recheck current permission and exact content before applying a cached snapshot.
        _, _, current_remote = self.registry().download(p["ref"]["name"], p["version"])
        require(package.hashes(package.unpack(current_remote)) == p["hashes"], "Remote content changed", "conflict")
        files = package.unpack(self.store.artifact(p["snapshot"]).read_bytes())
        require(package.hashes(files) == p["hashes"], "Installation snapshot changed", "conflict")
        self.replace_directory(p["target"], files, operation, p["previous"])
        item = {"id": p["installationId"], "ref": p["ref"], "context": p["context"], "target": p["target"], "hashes": p["hashes"], "version": p["version"],
                "selector": p["selector"], "snapshot": p["snapshot"], "loadState": "pending_host_verification", "lastOperationId": operation["id"]}
        self.data["installations"][item["id"]] = item
        return item

    def uninstall_plan(self, installationId):
        self.profile("install")
        item = self.data["installations"].get(installationId)
        require(item and item["ref"]["registryId"] == self.profile()["id"] and item["ref"]["namespaceId"] == self.profile()["namespaceId"], "Installation not found in this context", "not_found")
        require(item.get("context") == digest(self.profile()), "Installation context changed", "conflict")
        current = package.disk_hashes(item["target"])
        require(current == item["hashes"], "Local changes retained; resolve them before uninstalling", "conflict")
        return self.plan("uninstall", item["ref"], installationId=installationId, target=item["target"], localBaseline=current, previous=copy.deepcopy(item))

    def apply_uninstall(self, p, operation):
        require(package.disk_hashes(p["target"]) == p["localBaseline"], "Local changes retained", "conflict")
        operation.update(backup=self.snapshot(package.read_directory(p["target"])), target=p["target"], previous=p["previous"], beforeHashes=p["localBaseline"], afterHashes=None)
        self.store.save()
        displaced = Path(p["target"]).parent / (".nacos-remove-" + operation["id"])
        operation["displaced"] = str(displaced)
        self.store.save()
        os.rename(safe_path(p["target"]), displaced)
        operation["filesApplied"] = True
        self.store.save()
        shutil.rmtree(displaced)
        del self.data["installations"][p["installationId"]]
        return {"status": "uninstalled", "remoteChanged": False}

    def reconcile(self, operationId, version=None):
        op = self.data["operations"].get(operationId)
        require(op and op["status"] in ("running", "result_unknown"), "Only unresolved remote operations can be reconciled")
        p = self.data["plans"].get(op.get("planId"))
        require(p and p["context"] == digest(self.profile()), "No current-context plan for reconciliation", "conflict")
        require(p["kind"] in ("upload", "submit", "publish"), "No safe automatic reconciliation for this operation", "unsupported")
        r = self.registry("develop")
        meta = r.skill_meta(p["ref"]["name"])
        actual = version or (meta.get("editingVersion") if p["kind"] == "upload" else p["version"])
        require(actual, "Select the exact server version to compare; outcome remains unknown", "result_unknown")
        item = next((x for x in meta.get("versions", []) if x["version"] == actual), None)
        require(item, "Version unavailable; outcome remains unknown", "result_unknown")
        if p["kind"] == "upload":
            remote = package.unpack(r.draft_zip(p["ref"]["name"], actual))
            local = package.unpack(self.store.artifact(p["snapshot"]).read_bytes())
            require(semantic(remote) == semantic(local), "Remote content does not match the attempted upload", "result_unknown")
            self.data["bindings"][p["bindingId"]] = {"id": p["bindingId"], "path": p["localPath"], "context": p["context"], "ref": p["ref"],
                "policy": "explicit", "localHashes": p["localHashes"], "remoteVersion": actual, "remoteHashes": package.hashes(remote),
                "basePublishedVersion": ((p["remoteBaseline"] or {}).get("labels") or {}).get("latest")}
        else:
            expected = ("reviewing", "reviewed", "online") if p["kind"] == "submit" else ("online",)
            require(actual == p["version"] and item["status"] in expected, "Lifecycle transition cannot be confirmed", "result_unknown")
        op.update(status="completed", reconciled=True, result={"ref": p["ref"], "version": actual, "status": item["status"], "visibility": meta.get("scope")})
        p["status"] = "completed"
        self.store.save()
        return op

    def inspect_operation(self, operationId):
        op = self.data["operations"].get(operationId)
        require(op and self.operation_current(op), "Operation not found in current context", "not_found")
        return op

    def recover(self, operationId):
        """Explicit local recovery only; does not retry any remote mutation."""
        self.profile("install")
        op = self.data["operations"].get(operationId)
        require(op and (op.get("target") or op.get("configBackup")), "Operation has no local recovery")
        p = self.data["plans"][op["planId"]]
        require(p["context"] == digest(self.profile()), "Recovery context changed", "conflict")
        if op["status"] == "recovered": return op
        if op.get("configBackup"):
            return self.recover_config(op, p)
        require(op["action"] in ("install", "uninstall"), "Unsupported recovery action")
        target = safe_path(op["target"])
        current = package.disk_hashes(target)
        before, after = op.get("beforeHashes"), op.get("afterHashes")
        require(current is None or current == before or current == after, "Local modifications prevent recovery", "conflict")
        if op.get("backup"):
            # Restoring an installed version still requires current remote access.
            previous = op.get("previous")
            require(previous, "Cannot establish authorization for prior installation", "permission")
            self.registry().download(previous["ref"]["name"], previous["version"])
            files = package.unpack(self.store.artifact(op["backup"]).read_bytes())
            require(package.hashes(files) == before, "Recovery snapshot changed", "conflict")
            restore_op = self.store.operation("local_recovery", p["ref"])
            self.replace_directory(target, files, restore_op, None)
            restore_op.update(status="completed")
            self.data["installations"][previous["id"]] = {**previous, "loadState": "pending_host_verification"}
        else:
            if current is not None:
                require(current == after, "New target changed", "conflict")
                shutil.rmtree(target)
            self.data["installations"].pop(p.get("installationId"), None)
        for field in ("staging", "displaced"):
            path = op.get(field)
            if path and safe_path(path).exists():
                shutil.rmtree(safe_path(path))
        op["status"] = "recovered"
        self.store.save()
        return op

    def verify_skill(self, installationId):
        item = self.data["installations"].get(installationId)
        require(item and item.get("context") == digest(self.profile()), "Installation not found in current context", "not_found")
        try:
            self.registry().download(item["ref"]["name"], item["version"])
        except PluginError as exc:
            if exc.kind in ("authentication", "permission", "not_found"):
                item["loadState"] = "unavailable"
                self.store.save()
            raise
        require(package.disk_hashes(item["target"]) == item["hashes"], "Local content differs from installed baseline", "conflict")
        return {"installationId": installationId, "files": "verified", "remote": "readable", "loadState": item["loadState"],
                "next": "Verify Skill discovery and real use in the target Codex session; file checks do not prove loading"}


ACTIONS = {"configure", "status", "diagnose", "search", "scan", "onboarding", "select", "upload_plan", "install_plan", "publish_plan", "apply", "uninstall_plan", "inspect_operation", "recover", "verify_skill"}

ACTIONS.update({"discover", "connection_plan", "mcp_probe", "agent_send", "agent_task"})

ACTIONS.add("skill_status")

ACTIONS.update({"disconnect_plan", "reconcile"})
ACTIONS.update({"my_skills", "upload_preview"})
