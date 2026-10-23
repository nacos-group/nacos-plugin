# Codex 插件规范

本目录只维护 Codex 适配的设计、实现选择和验收状态。跨应用的资源身份、生命周期、
权限、同步和交互契约由[通用规范](../../specs/README.md)统一定义。

| 阅读内容 | 入口 |
| --- | --- |
| 资源加载、运行时、模板与执行适配 | [架构与实现](architecture-spec.md) |
| 页面信息架构、布局、视觉、交互与验收 | [资源中心 UI 设计](resource-center-ui-spec.md) |
| 本地对话初始化、侧栏预填、页面凭据与环境变量选择（dev.14；真实侧栏验收待完成） | [初始化与页面凭据设计](credential-onboarding-spec.md) |
| 跨 Agent 应用复用的入口、操作步骤、返回及状态语义 | [通用操作与状态规范](../../specs/resource-center-interaction-spec.md) |
| 已接入、我的资源、类型详情、行内浮层与单步操作结果 | [单状态 SVG 场景与交互规则](ui-storyboard.md) · [可点击图册](assets/ui/index.html) |
| manifest、产物、安装与发布渠道 | [打包与分发](distribution-spec.md) |
| 插件入口、页面、初始化及可选事件机制 | [可行性与验证边界](feasibility-spec.md) |
| 当前范围、实施状态、待办和决策 | [TODO 与排期](TODO.md) |

安装与开发从 [Codex 插件入口](../README.md)开始。其他 Agent 应用应在各自目录记录
适配与验证结果，Codex 的实现和测试结论不自动构成其他应用的支持声明。
本版 SVG 作为当前设计基线；交互规则归通用规范，Codex 的主题、尺寸与组件归本目录，
其他插件可以使用更贴近所在 Agent 应用的 CSS，保持相同操作语义。
