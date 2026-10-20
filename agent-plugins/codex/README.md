# Nacos AI Registry for Codex

将 Nacos AI Registry 接入 Codex，支持资源发现、管理与使用。本适配位于
`agent-plugins/codex/`，独立于 Nacos Server Java 插件，不加入根 Maven 构建。

本目录提供 Codex 适配规范和资源中心设计图册。通用操作规则由
`agent-plugins/specs/` 统一维护，Codex 的页面能力、主题、布局与工具映射由专属规范定义。
实现、工作流、安装指南、构建和验证代码与设计分开交付；规范中的源码路径用于定位后续实现。
TODO 记录设计、开发与验收状态，不表示本设计提交已经包含可安装产物。

| 内容 | 入口 |
| --- | --- |
| 通用产品与功能设计 | [通用规范](../specs/README.md) |
| Codex 架构、分发与可行性 | [专属规范](specs/README.md) |
| 资源中心布局、主题与组件 | [UI 设计](specs/resource-center-ui-spec.md) |
| 操作场景与 SVG | [图册说明](specs/ui-storyboard.md) · [可点击图册](specs/assets/ui/index.html) |
| 当前范围、待办和决策 | [TODO](specs/TODO.md) |

完整设计目标不等于已交付能力，未经实际验证的应用和服务器组合不声明支持。
私有测试环境配置、凭据与操作记录保存在仓库外，不进入规范或分发包。
