<!-- Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 -->

# Qoder 插件规范与适配边界

本目录维护 Qoder 的实现选择、版本兼容、验收证据和待办。当前代码版本为 `0.1.0-dev.8`，
详细功能及 ONB/CRED/DEF 映射以 [compatibility.json](compatibility.json) 为准。
安装、构建和历史验证说明见[开发预览记录](development-preview.md)。

通用契约位于仓库 `agent-plugins/specs/`；独立 Qoder 源码 ZIP 不包含其他应用和跨应用设计文档，
但保留本目录及全部运行/构建源码。规则的引用不要求运行时读取通用规范，也不引入 Codex 目录依赖。

## 1. 规范映射

| 通用规范 | Qoder 适配及边界 |
| --- | --- |
| `onboarding-spec.md`、`onboarding-acceptance-spec.md` | `nacos-setup` 使用当前 Qoder 原生问答；非敏感自定义值通过 Other 输入，取消不跳过，只有工具实际不可用才说明原因逐项退回对话。工具发现和调用映射到 `mcp_list/mcp_get/mcp_call`，不复制 Codex 的选择工具名。 |
| `credential-management-spec.md`、`platforms/macos-credential-store.md` | `nacos_credentials` 的 enter/clear 与 client/admin 面映射到本机 osascript 对话框和 SecItem。密码/Token 隐藏输入，不经过模型参数；存储 service、引用绑定、journal 和修订保护见兼容记录。无浏览器设置页或 Codex 加密桥接。 |
| `assembly-sync-spec.md` | 技能使用 `~/.qoder/skills` 或明确选定的项目目录；状态使用 `NACOS_QODER_HOME` 或 `~/.qoder/state/nacos-ai-registry`。MCP 绑定与 Qoder 原生注册分开验证，不能把绑定或探针计为原生工具已加载。 |
| `agent-interoperability-spec.md` | 当前为 A2A 0.3.0 JSONRPC 消费，需先保存绑定；原任务端点、独立认证、未知结果与取消按兼容记录约束。不承诺流式或本地 Agent 服务化。 |
| `capability-discovery-spec.md` | `nacos-find-capabilities` 承载普通任务触发条件，`nacos_search` 描述和 MCP `initialize.instructions` 重复同一语义；`discovery.installPolicy`（`ask` 缺省）保存在 profile 之外，计划与 apply 两处校验 `discoveryReuse`。免安装试用为 `nacos_preview_skill`、`nacos_mcp_trial`、`nacos_agent_trial`。`ask` 必须实际调用 `AskUserQuestion`，该要求同时出现在 SKILL.md 正文、`status.discovery.askInterface`、试用结果的 `reuse` 与相关工具描述里；同会话加载依赖用户重载 Skills 和 `query_mcp`/`manage_mcp`，插件没有刷新接口，不自动重启。 |
| `resource-center-ui-spec.md`、`resource-center-interaction-spec.md` | 当前是对话与工具工作流，页面未实现，应用页面能力未验证。未来采用通用操作语义和 Qoder 自身视觉风格，不要求照搬 Codex SVG。 |
| `distribution-spec.md` | `.qoder-plugin/plugin.json`（含 `logo` 与展示元数据）、`${QODER_PLUGIN_ROOT}`、Qoder 安装入口与独立 Python zipapp；不使用 Codex marketplace、manifest 或状态路径。图标为本目录自带的 `assets/nacos-icon.png` 副本，不引用其他适配目录。 |

系统用户名与 hostname 是本地默认标签，不代表服务端身份；默认命名空间 ID `public` 不表示资源公开。
这些语义继续服从通用规范，Qoder 只保留具体入口和措辞映射。

## 2. 发现契约的适配状态

dev.7 在 Qoder 侧独立实现了 `capability-discovery-spec.md` 的本地部分，dev.8 修正了询问形式的落点，
没有复用或修改 Codex 模块：

- [x] 入口与引导：`skills/nacos-find-capabilities/`（SKILL.md 承载触发条件，`references/task-completion.md`
      承载复用与试用流程），`nacos_search` 描述和 `initialize.instructions` 给出同一语义的静态提示，
      不携带配置或凭据，也不在初始化时访问资源中心。
- [x] 安装策略：`nacos_configure_discovery` 持久化 `ask | auto | never`，缺省和旧状态均为 `ask`；
      保存在 `profile` 之外，不改变授权上下文、已有资源归属或权限。模型不得自行改为 `auto`。
- [x] 询问形式：`ask` 必须实际调用 Qoder 原生 `AskUserQuestion`，仅在该工具未暴露或明确不可用时
      说明原因后退回对话。dev.8 把该要求同时写入 SKILL.md 正文、`status.discovery.askInterface`、
      三个试用结果的 `reuse`（`auto`/`never` 时不下发）以及偏好与试用工具描述，使规则在决策时点一定在上下文内。
- [x] 计划来源：`install_plan`/`connection_plan` 接受 `discoveryReuse`，创建与 apply 两处按当前策略校验；
      策略改为 `ask`/`never` 后旧自动计划被拒绝，已完成计划保持幂等。
- [x] 免安装试用：`nacos_preview_skill`（单文件 UTF-8，≤256 KiB）、`nacos_mcp_trial`（端点每次经注册中心
      重解析，工具枚举 ≤5 页/500 条）、`nacos_agent_trial`（不保存绑定，句柄绑定原端点）。操作记录只保留
      资源身份、状态和输入摘要。
- [x] 加载阶段：`status.host.sameSessionLoading` / `loadEvidence` 区分刷新已接受、运行时已连接、
      当前轮工具已暴露和业务调用成功；`nativeEntryName` 为 `nacos_<资源名>_<身份摘要>`，重命名已保存条目时
      返回 `previousEntryName` 与迁移说明，不静默覆盖或删除。

仍未完成、且不能用协议测试代替的部分：

- [ ] CD-01–07、CD-13–26、CD-28–34 需在真实 Qoder 新会话中逐项验证是否触发、是否误触发、候选依据、
      询问形式与任务是否继续，并记录应用/模型版本和次数，不继承 Codex 的结论。dev.7 的一次真实会话
      在试用后用对话文字询问复用，dev.8 的修正尚未在真实会话复测。
- [ ] 同会话加载仍取决于 Qoder 的 Skills 重载与原生连接器行为；当前没有插件可调用的刷新接口，
      相关指引未在真实应用中验收。

## 3. 验证记录归属

dev.8 自动化验证包含 171 项 checkout 测试（82 适配/核心、58 凭据、18 打包、13 发现与加载）、
隔离源码包测试、包和校验和检查、离线重建及清单展示元数据与图标断言；这些仅证明相应自动化层，
不代表真实 Keychain、Nacos、原生连接器、同会话加载或完整问答流程已经通过。
兼容记录保留各历史版本的证据边界；打包后安装/升级的补充结论见[开发预览记录](development-preview.md)，不能回填为打包前证据。

当前仍需按兼容记录逐项完成真实应用、系统存储、服务调用以及带配置/资源的卸载验收。
私有测试配置和操作轨迹留在仓库外；通用路线图只列适配状态和入口，不复制本适配的版本日志。
