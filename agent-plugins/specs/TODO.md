<!--
  Copyright 1999-2026 Alibaba Group Holding Ltd.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

# 通用路线图与适配分工

本文件记录跨 Agent 应用的功能方向和规范分工。完整功能编号 F01–F17 以
[功能规范](functional-spec.md)为准；各应用自行维护实现、待办、决策和验收结果，
一个适配通过验收不表示其他适配已经支持。

## 1. 通用演进方向

| 阶段 | 目标 | 通用约束 |
| --- | --- | --- |
| 基础接入 | Skill 生产与消费、显式双向更新、单中心接入、已有 MCP 与远端 Agent 消费、本地盘点。 | 区分资源读写、发布、应用加载和真实使用；保留来源、权限、冲突与恢复证据。 |
| 资源与治理扩展 | Prompt、AgentSpec、多中心、更多认证、企业配置与策略化更新。 | 模板按应用显式映射；后台进程与同步策略独立授权和验收。 |
| Agent 服务化 | 独立网关、隔离执行、任务映射、运行注册与活性。 | 不接管个人会话；注册成功不等于任务执行成功。 |
| 条件能力 | 资源中心页面、创建/更新提示。 | 页面由各应用实测决定；提示保留设计，是否实施另行评估。 |

## 2. 应用目录与实施入口

| 应用 | 源码与专属规范 | 当前状态 |
| --- | --- | --- |
| Codex | [源码](../codex/README.md)、[专属规范](../codex/specs/README.md)、[TODO](../codex/specs/TODO.md) | 开发预览；具体能力与剩余门槛见该适配记录。 |
| Qoder | [首版范围与门槛](../README.md#首版范围与剩余门槛)、能力及 ONB/CRED/DEF 映射 `agent-plugins/qoder/specs/compatibility.json` | 当前 dev.5 共 26 个工具，非敏感自定义配置也优先原生问答的 Other 输入，仅能力确实不可用才说明原因逐项降级；ONB-02/03 通用契约已同步。155 项 checkout 与实际源码 ZIP 隔离测试、包/校验和/完整源码检查、严格校验零错误/警告及字节一致离线重建通过，安装后实际交互待验收。旧 dev.4 未配置环境的卸载、MCP 移除和专用状态/缓存清理已验证；旧 dev.1–dev.4 本地 dist 已按用户要求清理，源码与历史验证记录保留。以下为历史 dev.4 验证：本机 macOS 推荐原生隐藏秘密录入与 keychain 保存/清除，environment 仅高级回退；默认命名空间（ID public）不是“公开”。2026-10-26 已完成 155 项测试（82 适配/核心、55 凭据、18 分发），全部通过；实际解压源码 ZIP 以 python -S -B、仅内置 YAML、空 HOME、无 Codex 目录也全部通过。构建/包检查、生成 *.zip.sha256 校验、ZIP 元数据/完整源码、隔离 zipapp CLI 与 initialize/tools-list/status、源码及安装包内源码离线重建字节一致、CLI 1.1.46 严格校验零错误/警告均通过，无 Codex 源码差异；文档输入同样纳入分发与离线重建检查。fake SecItem 查询标志/错误映射、Keychain 支撑的模拟 login/diagnose、下游别名隔离、绑定失败/上下文变更及事务/归属条目清除重试已本地验证；失败保存后内存重载持久状态，cleanupPending 在 status 和 credential/configure 结果可见。无真实用户秘密、实际 Keychain 或真实 Nacos 测试；CRED-10 配置后卸载/完整清理仍有限且待验收。dev.3 分步选项由用户在另一会话报告可用（未独立核验），命名空间措辞及仅环境变量体验未通过；本地 Qoder 进程的系统对话框可用性探测完成且超时干净退出，不是已安装插件录入或真实 Keychain 测试。dev.4 Desktop 安装/原生选项/对话框/Keychain/Nacos/连接器验收仍待完成；历史 dev.3 的 100 项（82+18）及 dev.2 的 25 工具/卸载记录保留，无浏览器/侧边页/资源中心，MCP 原生注册另行确认。 |
| WorkBuddy | 后续使用 `agent-plugins/workbuddy/` 与其 `specs/`。 | 尚无实现或兼容承诺。 |

新增适配时先验证应用能力，建立独立的 manifest、安装路径、刷新方式、运行依赖、
测试和产物入口。通用业务契约继续维护在本目录，应用专属技术细节不得回写为所有应用的要求。

## 3. 状态与决策归属

- 资源身份、生命周期、治理、同步与通用验收原则变更：更新本目录对应规范。
- 应用 API、包格式、页面与事件机制、版本矩阵及实现选择：更新 `<agent>/specs/`。
- 现有 T01–T34、D01–D12 及开发预览状态归入 Codex TODO，保留编号以便追踪。
- 后续适配自行记录待办与证据；共用实现时明确源码来源，避免复制后产生语义差异。
- 私有测试环境配置、操作脚本和运行轨迹保存在仓库外，不进入 CI、文档或发布包。

## 4. UI 通用化基线

- [x] 将当前 SVG 的入口、菜单、步骤、条件冲突、确认、结果与返回整理为[通用操作规范](resource-center-interaction-spec.md)，以 UIX-01–UIX-14 供各应用引用。
- [x] 在[通用 UI 规范](resource-center-ui-spec.md)中明确行为、能力适配和视觉适配分工，样式尽量跟随所在 Agent 应用；Codex 图稿与通用操作建立映射。
- [ ] 后续新增应用时独立完成 UIX 能力清单、主题/组件映射及实际入口验收；Qoder 对话适配已实现，页面未实现且宿主页面能力未验证，WorkBuddy 尚未实现。

本节完成的是设计归纳，不代表通用 UI 库或其他应用插件已经交付。

## 按任务意图发现能力

- [x] 定义[通用发现方案](capability-discovery-spec.md)：任务信号与主动发现时机、跨应用引导词、无有效结果回退、最小关键词、预算与授权交接，以及 CD-01–34 和跨模型/语言的比较方法。
- [x] 区分可达、应用加载与实际使用；完成任务后按真实安装状态询问本地复用，Skill/MCP 独立选择，尊重既有决定并保护原有资源。
- [ ] 各应用独立验证无插件提示的新会话行为；Codex dev.20 已实现发现入口和完成后复用指引，验证范围见其测试矩阵，其他应用不继承。
- [ ] 应用未提供当前会话原生刷新入口时，在专属 spec 记录依赖接口和同会话验收条件，保持可用的授权试用路径；Codex 对应 [DISC08](../codex/specs/TODO.md)，不把新会话成功等同于原会话热加载。

## 5. 初始化与凭据通用化

- [x] 提取[逐步初始化与设置交接](onboarding-spec.md)，包括默认目录、本地标识及已有配置保留。
- [x] 提取[凭据管理](credential-management-spec.md)与[macOS 系统实现](platforms/macos-credential-store.md)，分离应用输入入口、传输通道与系统存储。
- [x] 建立 [ONB/CRED/DEF 验收场景](onboarding-acceptance-spec.md)；Codex 保留工具映射、具体路径、视觉参数和执行结论。
- [ ] 各后续适配按实际应用/操作系统逐项验证并记录限制；复用规范不等于继承支持状态，也不默认共享凭据。

- [x] 通用发现规范补充 ask/auto/never、显式管理例外、先试用后复用、原生交互询问和当前会话优先使用（CD-28–34）；各应用单独验收。
