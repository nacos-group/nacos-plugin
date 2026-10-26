# Codex 插件规范

本目录只维护 Codex 适配的设计、实现选择和验收状态。跨应用的资源身份、生命周期、
权限、同步和交互契约由[通用规范](../../specs/README.md)统一定义。

| 阅读内容 | 入口 |
| --- | --- |
| 资源加载、运行时、模板与执行适配 | [架构与实现](architecture-spec.md) |
| Codex 页面入口、布局、主题、工具与验收映射 | [资源中心 UI 适配](resource-center-ui-spec.md) |
| 本地对话、侧栏、加密桥接工具及平台支持状态 | [Codex 初始化与凭据适配](credential-onboarding-spec.md) |
| 跨应用初始化问答、默认值与页面交接 | [通用初始化](../../specs/onboarding-spec.md) |
| 凭据生命周期、存储与通用验收场景 | [通用凭据规范](../../specs/credential-management-spec.md) · [通用验收](../../specs/onboarding-acceptance-spec.md) |
| 跨 Agent 应用复用的入口、操作步骤、返回及状态语义 | [通用操作与状态规范](../../specs/resource-center-interaction-spec.md) |
| Codex 页面状态与通用操作的对应关系 | [SVG 场景映射](ui-storyboard.md) · [可点击图册](assets/ui/index.html) |
| manifest、产物、安装与发布渠道 | [打包与分发](distribution-spec.md) |
| 插件入口、页面、初始化及可选事件机制 | [可行性与验证边界](feasibility-spec.md) |
| 当前范围、实施状态、待办和决策 | [TODO 与排期](TODO.md) |

安装与开发从 [Codex 插件入口](../README.md)开始。其他 Agent 应用应在各自目录记录
适配与验证结果，Codex 的实现和测试结论不自动构成其他应用的支持声明。
本版 SVG 作为当前设计基线；交互规则归通用规范，Codex 的主题、尺寸与组件归本目录，
其他插件可以使用更贴近所在 Agent 应用的 CSS，保持相同操作语义。
macOS Keychain 的系统实现维护在[通用平台规范](../../specs/platforms/macos-credential-store.md)，
本目录只保留 Codex 如何接入以及实际验证结论，不重复定义通用生命周期。
