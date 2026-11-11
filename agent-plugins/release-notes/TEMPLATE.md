<!-- Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 -->
<!-- Replace all {{...}} placeholders and remove empty change sections.
Retain explicit compatibility and pending-acceptance statements.
Do not publish this template as-is or reuse old test counts without verification. -->

# Nacos AI Registry Agent Plugins {{VERSION}}

This release includes the Codex and Qoder adapters at version {{VERSION}}.
{{ONE_SENTENCE_USER_VISIBLE_SUMMARY}}

## Features

- {{NEW_USER_CAPABILITY_AND_SUPPORTED_SCOPE}}

## Improvements

- {{IMPROVED_BEHAVIOR_AND_PRACTICAL_EFFECT}}

## Fixes

- {{TRIGGER_PREVIOUS_BEHAVIOR_AND_FIXED_RESULT}}

## Upgrade from {{PREVIOUS_VERSION}}

- Upgrade through the original installation source and retain existing configuration,
  credentials, installed Skills and connections.
- {{MIGRATION_REQUIREMENTS_PLAN_COMPATIBILITY_AND_RELOAD_STEPS_OR_EXPLICIT_NONE}}
- {{BREAKING_CHANGES_OR_UNCHANGED_SUPPORT_BOUNDARIES}}

## Verification and CI

- Local release checks: {{CODEX_PYTHON_COUNT}} Codex Python tests,
  {{CODEX_NODE_COUNT}} Codex Node tests and {{QODER_PYTHON_COUNT}} Qoder Python tests passed.
- Both adapter package checks passed, including {{ACTUAL_PACKAGE_CHECK_COVERAGE}}.
- [Agent plugin CI]({{CI_RUN_URL}}) passed {{CI_JOB_COUNT}} required jobs on
  {{CI_ENVIRONMENTS}}. CI head: `{{CI_HEAD_SHA}}`.
- Real Nacos integration: {{INTEGRATION_CASE_COUNT}} cases covering {{ACTUAL_COVERAGE}};
  Nacos source `{{NACOS_COMMIT}}` ({{NACOS_VERSION}}), with {{AUTH_MODES}}.
  {{TEST_FIXTURE_AND_VERIFICATION_BOUNDARIES}}

Automated checks do not establish native host loading or successful use in every
desktop, operating system or model. See the pending acceptance items below.

## Compatibility

- Runtime and execution location: {{PYTHON_MINIMUM_AND_LOCAL_OR_REMOTE_EXECUTION_SCOPE}}.
- Nacos API compatibility: {{VERIFIED_SERVER_SCOPE}}.
- Operating systems and credential storage: {{MACOS_LINUX_WINDOWS_SUPPORT_AND_LIMITATIONS}}.
- Authentication: {{SUPPORTED_PROVIDERS_AND_UNSUPPORTED_PROVIDERS}}.
- Host UI and protocols: {{CODEX_QODER_UI_MCP_A2A_SUPPORT_AND_LIMITATIONS}}.
- Native loading: {{SAME_SESSION_SKILL_MCP_LOADING_AND_RELOAD_LIMITATIONS}}.

## Pending host acceptance

{{LIST_UNEXECUTED_BLOCKED_OR_NOT_APPLICABLE_ITEMS_AND_THEIR_IMPACT}}

Record UI, credential permissions and restart behavior, native loading, model
interactions, and configured upgrade/uninstall separately for each host. If all
required items passed, replace this paragraph with the actual scope and evidence;
do not infer completion from CI or a successful package build.

Acceptance record: [host-specific checklist]({{ACCEPTANCE_RECORD_URL}}).

## Distribution files

This release contains four ZIPs and four matching `.zip.sha256` files, for eight
attachments. Use the host-specific installation ZIP to install the plugin.
GitHub's automatically generated Source code archives are separate from the
host-specific source packages below.

| Adapter | Install archive | Source archive |
| --- | --- | --- |
| Codex | `nacos-ai-registry-{{VERSION}}.zip` | `nacos-ai-registry-{{VERSION}}-source.zip` |
| Qoder | `nacos-ai-registry-qoder-{{VERSION}}.zip` | `nacos-ai-registry-qoder-{{VERSION}}-source.zip` |

After downloading a ZIP and its checksum file, verify it in that directory:

```sh
# macOS; replace the name for Qoder or a source archive.
shasum -a 256 -c nacos-ai-registry-{{VERSION}}.zip.sha256
# Linux equivalent: sha256sum -c <archive>.zip.sha256
```

Installation: [Codex](https://github.com/nacos-group/nacos-plugin/blob/nacos-ai-registry-v{{VERSION}}/agent-plugins/codex/README.md)
and [Qoder](https://github.com/nacos-group/nacos-plugin/blob/nacos-ai-registry-v{{VERSION}}/agent-plugins/qoder/README.md).
This GitHub Release distributes the packages; it does not submit either adapter to
a host's public plugin directory.

## Release verification

- Tag: `nacos-ai-registry-v{{VERSION}}`.
- Both adapters were rebuilt from clean merged commit `{{RELEASE_COMMIT}}`;
  both installation archives report this commit, version `{{VERSION}}` and `dirty: false`.
- {{CI_HEAD_VS_RELEASE_COMMIT_RELATIONSHIP_AND_CONTENT_COMPARISON}}
- Both source packages correspond to the bundled source in their installation packages.
- All eight attachment names, sizes and SHA-256 digests were checked against the
  uploaded draft before publication and verified again after publication.
- {{PENDING_ACCEPTANCE_SUMMARY_WITHOUT_CLAIMING_UNPERFORMED_CHECKS}}
