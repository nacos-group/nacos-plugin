# Nacos AI Registry Agent Plugins

为 coding agent / personal agent 提供 Nacos AI Registry 接入，发现、管理和使用 agentic 资源。
各 Agent 应用的插件按目录独立维护，通用资源契约集中在 `specs/`。

目录分工如下；实现、测试和构建目录随对应代码交付。

```text
agent-plugins/
├── README.md
├── specs/                 # 通用功能、资源契约、治理与路线图
└── codex/                 # Codex 插件实现与构建入口
    ├── plugin.json
    ├── mcp.json
    ├── skills/
    ├── src/
    ├── tests/
    ├── scripts/
    ├── docs/
    └── specs/             # Codex 适配、分发、验证与 TODO
```

后续 Qoder、WorkBuddy 等适配分别放在同级的 `qoder/`、`workbuddy/` 目录，并在各自
`specs/` 下维护应用专属设计。当前维护 Codex 的专属规范，其他应用尚未声明支持。

| 阅读内容 | 入口 |
| --- | --- |
| 通用产品与功能设计 | [规范概览](specs/README.md) |
| 跨应用演进与分工 | [通用路线图](specs/TODO.md) |
| Codex 适配设计与兼容边界 | [Codex 设计](codex/README.md) |
| Codex 实现与验收状态 | [Codex TODO](codex/specs/TODO.md) |

各适配独立构建和发布，不加入根 Maven 构建。插件源码、内置工作流与合成样例可以随包
交付；用户资源、凭据、私有测试环境配置及操作记录留在用户环境。
