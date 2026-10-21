# Nacos AI Registry for Codex

将 Nacos AI Registry 接入 Codex。本组件位于 `agent-plugins/codex/`，独立于
仓库中的 Nacos Server Java 插件，不需要复制 JAR 到 Nacos，也不由根 Maven 构建。

当前提供 `0.1.0-dev.10` 首版验收候选的源码与可安装包；P0/P1 的实现覆盖和剩余发布门槛见 TODO。
完整设计目标不等于本版已交付能力。
首期包含 Skill 生产/消费、显式双向更新和初始化盘点，以及已有 MCP/远端 Agent 的发现
与调用。[简洁工作台](specs/resource-center-ui-spec.md)已按选定图册重构为三主视图、
类型专属详情和独立设置；本地自动测试与浏览器交互已验证，基础功能经使用者自测可用，
现进入首版验收。完整内嵌闭环与首次连接三步向导等差距继续在 TODO 中单列。
分层结论见[测试矩阵](specs/test-matrix.md)。
创建后提醒和 Hooks 不纳入首期。

| 内容 | 入口 |
| --- | --- |
| 产品与完整设计 | [通用规范](../specs/README.md) |
| Codex 适配设计 | [专属规范](specs/README.md) |
| 当前范围、待办和决策 | [TODO](specs/TODO.md) |
| 来源、仓库与迁移检查 | [迁移记录](docs/migration.md) |
| 源码、安装包与兼容要求 | [打包分发](specs/distribution-spec.md) |

版本独立采用 SemVer，tag 为 `nacos-ai-registry-v<version>`。不沿用 Server 插件的版本
映射。运行依赖与支持边界见兼容说明，私有测试环境信息不进入仓库；未经验证的 Agent 应用与服务器组合不声明支持。
仓库只保存插件源码、内置工作流和隔离样例，用户业务资源和凭据留在用户环境。

## 安装与开发

- [本地安装、初始化和恢复](docs/installation.md)
- [开发、测试与打包](docs/development.md)
- [资源中心页面与入口排查](docs/resource-center.md)
- [兼容范围与发布门槛](docs/compatibility.md)

源码入口为 `src/nacos_registry/`，工作流在 `skills/`，manifest 为根目录的 `plugin.json`。
构建生成独立 zipapp、安装 ZIP 和源码 ZIP。提供对话向导、MCP 工具及资源中心页面；各项验收状态见 TODO。
