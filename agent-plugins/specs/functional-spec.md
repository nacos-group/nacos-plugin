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

# 功能规范

本文定义产品完整目标，不表示功能已经实现。跨应用方向见[通用路线图](TODO.md)，
具体实现阶段、范围和待决策事项记录在各应用的 TODO 中。各项功能使用稳定编号，便于追踪。

## 1. 使用者与交互原则

| 使用者 | 主要需求 |
| --- | --- |
| 企业员工或个人使用者 | 表达业务目标，找到有权限使用的资源，并完成任务。 |
| 资源开发者 | 开发、验证、更新并发布可复用的 agentic 资源。 |
| 企业资源管理员 | 配置资源入口、发布规则、授权范围和统一更新策略。 |
| 插件维护者与宿主适配者 | 维护协议兼容、宿主支持、源码和可安装发布包。 |

同一使用者可以具有多种角色，实际权限由 Nacos、目标服务和宿主共同约束。
普通使用流程必须优先呈现业务用途、来源、所需输入和可用状态；协议名称、内部版本字段、
文件路径等技术信息放在可展开的详情或诊断中。不得要求员工手写 API 请求才能完成正常使用。

## 2. 完整功能清单

| 编号 | 功能 | 行为约束 | 主要设计 |
| --- | --- | --- | --- |
| F01 | 连接与初始化 | 配置多个个人/企业入口，选择 namespace，完成身份与连通诊断。 | [接入与治理](connection-governance-spec.md) |
| F02 | 资源发现 | 按意图、名称、类型和业务标签搜索可见资源，返回可解释的选择结果。 | [资源管理](resource-management-spec.md) |
| F03 | 资源开发与发布 | 新增、更新、校验、提交和发布 Skill、Prompt、AgentSpec；记录确切版本与结果。 | [资源管理](resource-management-spec.md) |
| F04 | Skill 使用 | 获取包、校验结构、安装到支持的宿主作用域，并验证是否可发现。 | [装配与更新](assembly-sync-spec.md) |
| F05 | Prompt 使用 | 获取版本化模板，校验变量，在指定任务中渲染并使用。 | [装配与更新](assembly-sync-spec.md) |
| F06 | AgentSpec 使用 | 解释支持的模板，解析资源依赖，生成可审阅的宿主装配计划。 | [装配与更新](assembly-sync-spec.md) |
| F07 | MCP 接入 | 发现服务、解析可用连接、绑定凭据、装配并验证工具能力。 | [装配与更新](assembly-sync-spec.md) |
| F08 | 远端 Agent 消费 | 搜索、发现、按支持的协议调用远端 Agent，跟踪结果及取消。 | [Agent 互联](agent-interoperability-spec.md) |
| F09 | Agent 注册与服务化 | 管理 Agent 定义；将具备实际执行入口的本地 Agent 服务注册、续租和注销。 | [Agent 互联](agent-interoperability-spec.md) |
| F10 | 持续更新与恢复 | 按策略检测变化、处理本地冲突、更新依赖、回滚和卸载托管内容。 | [装配与更新](assembly-sync-spec.md) |
| F11 | 企业治理 | 使用服务端身份与可见性，落实可信入口、受控发布和资源使用策略。 | [接入与治理](connection-governance-spec.md) |
| F12 | 多宿主适配 | 共享业务核心，按宿主能力转换技能、提示词、模板、工具与交互。 | [架构与宿主适配](architecture-spec.md) |
| F13 | 源码与插件分发 | 从同一源码版本生成发布包，支持安装、升级和不同分发渠道。 | [打包与分发](distribution-spec.md) |
| F14 | 状态与诊断 | 展示真实的连接、版本、装配和执行状态，提供不含凭据的诊断。 | [架构与宿主适配](architecture-spec.md) |
| F15 | 资源中心页面 | 在支持图形能力的应用内提供已接入、发现资源和我的资源视图，以及独立设置/本地技能流程，复用工具的状态与操作。 | [资源中心页面](resource-center-ui-spec.md) |
| F16 | 本地资源盘点与托管 | 在初始化或按需盘点宿主资源，让用户选择上传、映射与同步策略。 | [本地资源托管](local-resource-onboarding-spec.md) |
| F17 | 创建与更新提示（可选候选） | 保留变化感知、上传/发布提示和去重设计；是否实施另行评估，启用后须保留用户忽略选择。 | [本地资源托管](local-resource-onboarding-spec.md) |

## 3. 资源边界

| 资源 | 管理对象 | 使用结果 |
| --- | --- | --- |
| Agent | 目录元数据、版本化调用定义、独立的运行地址 | 可按声明协议调用的远端服务。 |
| Skill | SKILL.md 与引用资源组成的版本包 | 宿主可发现并按需使用的技能。 |
| Prompt | 模板、变量和版本 | 当前任务选定并填充变量的提示内容。 |
| AgentSpec | manifest 与资源文件组成的版本包 | 经宿主适配器解释的模板和依赖装配计划。 |
| MCP | 服务定义、工具描述、地址与版本 | 宿主或明确启用的代理能够连接的 MCP 服务。 |

AgentSpec 是模板，Agent 是可调用服务；模板安装本身不创建运行地址。资源下载、宿主加载、
远端连接和实际任务执行是不同结果，必须分别验证。MCP 定义管理遵循 Nacos 现有治理契约；
本产品的 MCP 核心要求是发现与装配，不据此扩大为完整的 MCP 运维控制台。

## 4. 自动化边界

- 自动发现、版本解析和差异生成可以由用户意图触发，不要求用户了解资源类型。
- 自动写入、更新、远端调用和发布必须落在已授权的入口、资源、作用域及操作范围内；
  已有授权覆盖时不重复请求确认。扩大权限或无法消解本地冲突时才需要新的决定。
- 内容同步不得隐式运行下载包的脚本，不得修改宿主安全策略来使装配成功。
- 插件只能承诺支持矩阵内的行为，不得把“文件已写入”标记为“宿主已生效”。
- 后台同步与对外服务必须有明确进程所有者和关闭语义，不能依赖模型持续对话维持活性。

## 5. 功能验收原则

| 场景 | 验收要求 |
| --- | --- |
| 员工首次使用 | 给定已授权的企业入口，仅通过业务描述和必要输入即可发现并使用一项资源。 |
| 资源发布 | 能查明草稿、审核和上线状态；上线后由消费者读取确切目标版本。 |
| 资源使用 | 可追溯来源、解析版本、目标作用域、依赖和生效状态。 |
| 更新冲突 | 保留本地修改，说明冲突文件和解决选项，不产生无记录覆盖。 |
| 权限变化 | 撤权或资源下线不会被误报为网络错误或持续展示为可用。 |
| 宿主差异 | 不支持的能力返回明确限制和可选路径，不静默丢弃模板含义。 |
| 本地托管 | 盘点不隐含上传；创建提醒、上传草稿和发布分别授权，忽略与去重规则有效。 |
| 页面管理 | 在支持的宿主内完成搜索、接入、查看和更新；页面与对话反映同一资源与操作状态。 |
| 插件分发 | 干净环境能够按说明安装，发布包不依赖维护者的机器路径或凭据。 |

本规范不定义新的 Nacos 资源类型、发布状态或权限体系，不要求更改既有服务端契约。
若后续设计需要改变这些行为，必须另行讨论并同步更新对应 Nacos 领域规范。
