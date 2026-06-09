# skills.sh AI Importer Plugin

Imports Skill resources from the skills.sh API into the Nacos AI resource import flow.

## Build

```bash
mvn -pl nacos-ai-importer-plugin-ext/nacos-skills-sh-ai-importer-plugin -am package
```

Copy `target/nacos-skills-sh-ai-importer-plugin.jar` to the Nacos `plugins` directory.

## Configuration

```properties
nacos.plugin.ai.importer.skills.skills-sh.enabled=true
nacos.plugin.ai.importer.skills.skills-sh.endpoint=https://skills.sh
nacos.plugin.ai.importer.skills.skills-sh.token=${VERCEL_OIDC_TOKEN}
```

Optional properties:

```properties
nacos.plugin.ai.importer.skills.skills-sh.source-id=skills-sh
nacos.plugin.ai.importer.skills.skills-sh.display-name=skills.sh
nacos.plugin.ai.importer.skills.skills-sh.connect-timeout-ms=3000
nacos.plugin.ai.importer.skills.skills-sh.read-timeout-ms=10000
nacos.plugin.ai.importer.skills.skills-sh.max-item-count=500
nacos.plugin.ai.importer.skills.skills-sh.max-artifact-size=10485760
```

HTTP and private-network endpoints are rejected by default. Operators can opt in for controlled private deployments:

```properties
nacos.plugin.ai.importer.skills.skills-sh.allow-http=true
nacos.plugin.ai.importer.skills.skills-sh.allow-private-network=true
```
