# skills.sh AI Importer Plugin

Imports Skill resources from the authenticated skills.sh v1 API into the Nacos AI resource
import flow.

## Build

```bash
mvn -pl nacos-ai-importer-plugin-ext/nacos-skills-sh-ai-importer-plugin -am package
```

Copy `target/nacos-skills-sh-ai-importer-plugin.jar` to the Nacos `plugins` directory.

## Configuration

```properties
nacos.plugin.ai-resource-import.skills-sh-authenticated.enabled=true
nacos.plugin.ai-resource-import.skills-sh-authenticated.endpoint=https://skills.sh
nacos.plugin.ai-resource-import.skills-sh-authenticated.token=${SKILLS_SH_TOKEN}
```

Optional properties:

```properties
nacos.plugin.ai-resource-import.skills-sh-authenticated.display-name=skills.sh Authenticated
nacos.plugin.ai-resource-import.skills-sh-authenticated.description=Import Skills from authenticated skills.sh v1 APIs.
nacos.plugin.ai-resource-import.skills-sh-authenticated.connect-timeout-ms=3000
nacos.plugin.ai-resource-import.skills-sh-authenticated.read-timeout-ms=10000
nacos.plugin.ai-resource-import.skills-sh-authenticated.max-item-count=500
nacos.plugin.ai-resource-import.skills-sh-authenticated.max-artifact-size=10485760
```

HTTP and private-network endpoints are rejected by default. Operators can opt in for controlled private deployments:

```properties
nacos.plugin.ai-resource-import.skills-sh-authenticated.allow-http=true
nacos.plugin.ai-resource-import.skills-sh-authenticated.allow-private-network=true
```

The managed source id is `skills-sh-authenticated`, which is intentionally distinct from
the built-in public `skills-sh` importer. The legacy
`nacos.plugin.ai.importer.skills.skills-sh.*` item keys are retained as configuration aliases.
