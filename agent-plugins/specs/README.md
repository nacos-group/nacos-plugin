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

# Nacos AI Registry 通用规范

Nacos Personal Agent Plugin 为各类 coding agent 和 personal agent 提供快速接入
Nacos AI Registry 的插件，让用户通过自己熟悉的 Agent 完成 agentic 资源的开发、
发现、使用和持续更新，减少接入配置、资源选择与运行装配的成本。

面向企业，插件帮助企业将自有、内部可接入、受权限和发布流程管控的 agentic 资源
提供给员工。员工可以直接表达业务需求，由 Agent 帮助发现合适的资源并完成使用准备，
降低不熟悉技术型 Agent 的员工使用内部能力的门槛。面向个人，插件提供统一的个人资源
入口，让技能、提示词、模板、工具和远端 Agent 能够跨任务、跨 Agent 应用复用。

Nacos 负责资源的统一管理与治理；插件负责把这些资源接入用户的 Agent 工作环境。
本规范同时覆盖 coding agent 与 personal agent，共享资源语义，由应用适配层处理
不同产品的安装、交互、配置与执行方式。

本目录维护跨 Agent 应用的功能、资源与治理契约，[通用路线图](TODO.md)说明演进方向。
各应用的安装、实现和验收记录维护在其专属目录；当前入口为 [Codex 规范](../codex/specs/README.md)。
安装与开发从[插件入口](../README.md)开始。原 Nacos 规范与源码使用固定提交的跨仓库链接。

## 能力概览

| 能力 | 用户获得的结果 |
| --- | --- |
| 快速接入 | 配置个人或企业资源入口，识别当前可用资源和权限。 |
| 发现与使用 | 按业务意图发现 Agent、Skill、Prompt、AgentSpec 和 MCP，并完成使用准备。 |
| 资源中心页面 | 在支持的 Agent 应用内查看已接入和个人资源，搜索并接入可用能力。 |
| 开发与共享 | 将资源沉淀为版本，完成新增、更新和受管控发布。 |
| 本地资源托管 | 盘点已有资源，选择上传或托管方式，维护本地与远端的关联。 |
| 装配与更新 | 解析依赖、装配本地能力，跟踪更新并保留可恢复的版本。 |
| Agent 互联 | 调用远端 Agent，也可将受控的本地 Agent 执行能力发布为远端服务。 |
| 多应用适配与分发 | 在不同 Agent 应用中复用核心能力，面向个人、同事和外部用户分发插件。 |

## 规范导航

| 阅读内容 | 入口 |
| --- | --- |
| 完整功能范围与验收约束 | [功能规范](functional-spec.md) |
| 模块职责、资源身份和应用扩展边界 | [架构与应用适配](architecture-spec.md) |
| 个人接入、企业入口、身份和权限 | [接入与治理](connection-governance-spec.md) |
| 初始化问答、执行位置、页面交接、默认目录与本地标识 | [初始化与设置交接](onboarding-spec.md) |
| 安全输入、凭据来源、隔离、保存/替换/清除和可选加密通道 | [凭据管理](credential-management-spec.md) |
| 跨应用复用的系统凭据存储实现 | [macOS 系统钥匙串](platforms/macos-credential-store.md) |
| 初始化、凭据生命周期与默认值的公共测试场景 | [通用验收](onboarding-acceptance-spec.md) |
| 首次资源盘点、托管选择与创建后提示 | [本地资源托管](local-resource-onboarding-spec.md) |
| 已接入、发现、我的资源、设置与本地技能的交互规则 | [资源中心 UI 与交互](resource-center-ui-spec.md) |
| 逐项操作的入口、状态、执行影响、返回与异常；跨应用复用 | [资源中心通用操作与状态](resource-center-interaction-spec.md) |
| 资源搜索、开发、版本与发布 | [资源管理](resource-management-spec.md) |
| Skill、Prompt、AgentSpec、MCP 的使用与持续同步 | [装配与更新](assembly-sync-spec.md) |
| 远端 Agent 消费与本地 Agent 服务化 | [Agent 互联](agent-interoperability-spec.md) |
| 源码、插件包、安装和发布渠道 | [打包与分发](distribution-spec.md) |
| 实现原理、已有依据和技术验证点 | [可行性分析](feasibility-spec.md) |
| 跨应用演进方向与适配分工 | [通用路线图](TODO.md) |

UI 规范与操作规范共同定义跨应用行为；`<agent>/specs/` 负责实际能力、视觉风格和工具映射。
后续 Qoder、WorkBuddy 可以采用贴近各自应用的 CSS 与组件，保持操作语义一致；无需照搬
Codex 图稿的颜色、尺寸或技术栈。当前 SVG 是 Codex 的设计基线，不是各应用支持证明。

初始化与凭据按三层维护：本目录定义通用流程和行为；`platforms/` 定义操作系统实现；
`<agent>/specs/` 记录应用入口、工具/字段映射、具体路径、视觉设计和验收结果。
复用系统存储实现不默认共享各应用的凭据，复用验收场景不继承其他应用的通过状态。
