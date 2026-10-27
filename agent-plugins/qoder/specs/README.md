<!-- Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 -->

# Qoder 插件规范与适配边界

本目录维护 Qoder 的实现选择、版本兼容、验收证据和待办。当前代码版本为 `0.1.0-dev.6`，
详细功能及 ONB/CRED/DEF 映射以 [compatibility.json](compatibility.json) 为准。
安装和构建入口见仓库 `agent-plugins/README.md` 的 Qoder 章节。

通用契约位于仓库 `agent-plugins/specs/`；独立 Qoder 源码 ZIP 不包含其他应用和跨应用设计文档，
但保留本目录及全部运行/构建源码。规则的引用不要求运行时读取通用规范，也不引入 Codex 目录依赖。

## 1. 规范映射

| 通用规范 | Qoder 适配及边界 |
| --- | --- |
| `onboarding-spec.md`、`onboarding-acceptance-spec.md` | `nacos-setup` 使用当前 Qoder 原生问答；非敏感自定义值通过 Other 输入，取消不跳过，只有工具实际不可用才说明原因逐项退回对话。工具发现和调用映射到 `mcp_list/mcp_get/mcp_call`，不复制 Codex 的选择工具名。 |
| `credential-management-spec.md`、`platforms/macos-credential-store.md` | `nacos_credentials` 的 enter/clear 与 client/admin 面映射到本机 osascript 对话框和 SecItem。密码/Token 隐藏输入，不经过模型参数；存储 service、引用绑定、journal 和修订保护见兼容记录。无浏览器设置页或 Codex 加密桥接。 |
| `assembly-sync-spec.md` | 技能使用 `~/.qoder/skills` 或明确选定的项目目录；状态使用 `NACOS_QODER_HOME` 或 `~/.qoder/state/nacos-ai-registry`。MCP 绑定与 Qoder 原生注册分开验证，不能把绑定或探针计为原生工具已加载。 |
| `agent-interoperability-spec.md` | 当前为 A2A 0.3.0 JSONRPC 消费，需先保存绑定；原任务端点、独立认证、未知结果与取消按兼容记录约束。不承诺流式或本地 Agent 服务化。 |
| `resource-center-ui-spec.md`、`resource-center-interaction-spec.md` | 当前是对话与工具工作流，页面未实现，应用页面能力未验证。未来采用通用操作语义和 Qoder 自身视觉风格，不要求照搬 Codex SVG。 |
| `distribution-spec.md` | `.qoder-plugin/plugin.json`、`${QODER_PLUGIN_ROOT}`、Qoder 安装入口与独立 Python zipapp；不使用 Codex marketplace、manifest 或状态路径。 |

系统用户名与 hostname 是本地默认标签，不代表服务端身份；默认命名空间 ID `public` 不表示资源公开。
这些语义继续服从通用规范，Qoder 只保留具体入口和措辞映射。

## 2. 新通用发现契约的适配待办

本次合并新增的 `capability-discovery-spec.md` 不自动改变 Qoder dev.6 的行为。当前有显式搜索和
资源管理工具，但没有 Codex 的 `nacos-find-capabilities` 工作流、安装策略设置、无安装试用工具
或 App Server 刷新接口。独立的 `src/nacos_registry/` 也不会随 Codex 同名模块自动升级。

- [ ] 按 CD-01–22 设计 Qoder 的普通任务触发入口，验证是否会发现及是否跳过，不强制模型选用 Nacos。
- [ ] 映射 ask/auto/never、显式管理例外和有效使用后复用；询问使用 Qoder 当前可用的原生选择工具。
- [ ] 按 CD-32 声明 Skill/MCP/Agent 的无安装使用能力及限额；不能将当前先保存绑定的流程计为免安装试用。
- [ ] 验证同一会话原生注册/加载/刷新能力及工具目录变化；当前新会话验证指引不能算 CD-34 通过。
- [ ] 核对原生服务名称、冲突保护和兼容迁移是否满足装配规范 §6.1，按 Qoder 接口制定格式。
- [ ] 为上述能力建立自身的配置兼容、测试矩阵及真实应用证据，不继承 Codex 的测试结论。

## 3. 验证记录归属

dev.6 历史验证包含 155 项 checkout/隔离源码包测试、包和校验和检查、离线重建及 CLI 严格校验；
这些仅证明相应自动化层，不代表真实 Keychain、Nacos、原生连接器或完整问答流程已经通过。
兼容记录保留各历史版本的证据边界；打包后安装/升级的补充结论见仓库入口文档，不能回填为打包前证据。

当前仍需按兼容记录逐项完成真实应用、系统存储、服务调用以及带配置/资源的卸载验收。
私有测试配置和操作轨迹留在仓库外；通用路线图只列适配状态和入口，不复制本适配的版本日志。
