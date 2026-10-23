# SkillHub AI Importer Plugin

Imports Skill resources from an authenticated SkillHub registry into the Nacos AI resource
import flow.

Compatible with **Nacos 3.2.x** (`AiResourceImportServiceBuilder` + `AiResourceImportSourceProvider`).

## Build

```bash
mvn -pl nacos-ai-importer-plugin-ext/nacos-skillhub-ai-importer-plugin -am package
```

Copy `target/nacos-skillhub-ai-importer-plugin-*.jar` to the Nacos `plugins` directory.

## Configuration

```properties
nacos.plugin.ai.importer.skills.skillhub.enabled=true
nacos.plugin.ai.importer.skills.skillhub.endpoint=https://skillhub.example.com
nacos.plugin.ai.importer.skills.skillhub.token=${SKILLHUB_TOKEN}
```

`namespace` is **optional**. When omitted, search defaults to **`global`**.

| Search box input | Meaning |
|---|---|
| *(empty)* / `alpha` | search in `global` (or config default namespace) |
| `@team-x` | list all published skills in `team-x` |
| `@team-x alpha` | filter by keyword `alpha` in `team-x` |
| `@team-x/alpha` | same as above |
| `team-x--alpha` | namespace=`team-x`, keyword=`alpha` |

Optional default namespace override (used when the query has no `@ns`):

```properties
nacos.plugin.ai.importer.skills.skillhub.namespace=global
```

Other optional properties:

```properties
nacos.plugin.ai.importer.skills.skillhub.source-id=skillhub
nacos.plugin.ai.importer.skills.skillhub.display-name=SkillHub
nacos.plugin.ai.importer.skills.skillhub.description=Import Skills from an authenticated SkillHub registry.
nacos.plugin.ai.importer.skills.skillhub.connect-timeout-ms=3000
nacos.plugin.ai.importer.skills.skillhub.read-timeout-ms=30000
nacos.plugin.ai.importer.skills.skillhub.max-item-count=500
nacos.plugin.ai.importer.skills.skillhub.max-artifact-size=10485760
nacos.plugin.ai.importer.skills.skillhub.redirect-host-map=minio:192.168.84.4
nacos.plugin.ai.importer.skills.skillhub.allow-http=true
nacos.plugin.ai.importer.skills.skillhub.allow-private-network=true
```

The importer type / plugin name is `skillhub`.

## Download API (iflytek/skillhub)

Validation / import downloads packages using SkillHub's current routes (in order):

1. `GET /api/v1/skills/{namespace}/{slug}/versions/{version}/download`
2. `GET /api/v1/skills/{namespace}/{slug}/download`
3. `GET /api/v1/download/{canonicalSlug}?version={version}` (ClawHub-compatible; may 302)
4. `GET /api/v1/download?slug={canonicalSlug}&version={version}`

Redirects to object storage (e.g. MinIO) are followed with optional `redirect-host-map` rewriting.
Redirects that stay on the SkillHub API keep the Bearer token.
