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

# Codex 可行性与验证边界

本文保留 2026-10-19 原设计阶段的 Codex 官方文档核对记录与技术推导，不表示其中能力
已经运行验收。Nacos 协议与跨应用原理见[通用可行性分析](../../specs/feasibility-spec.md)；
当前实现状态与未通过项见 [TODO](TODO.md) 和兼容说明（实现交付时见 `agent-plugins/codex/docs/compatibility.md`）。

## 1. 插件入口

Codex 的官方插件机制支持 Skills 与 bundled MCP 配置，这为本地适配提供了现成入口。
这个证据只适用于已核对的宿主，不证明其他 Agent 使用同一种 manifest 或刷新机制。
依据：[插件架构](https://developers.openai.com/plugins/concepts/plugins)、
[本地 MCP 包](https://developers.openai.com/plugins/deploy/desktop-only)。

## 2. 资源刷新

条件查询只能证明资源内容状态，不证明宿主已经重新加载。官方文档说明 Codex 会检测
本地 Skill 变化，但仍提供未生效时重启的处理路径；MCP 连接配置也有独立宿主生命周期。
因此“资源更新”和“宿主生效”必须有两份证据，无法直接承诺所有能力在当前会话无缝热更新。
依据：[Skill 监听契约](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/skill-spec.md)、
[Codex Skills](https://learn.chatgpt.com/docs/build-skills)、
[Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)。

## 3. 执行网关（后续能力）

Codex app-server 提供会话创建/继续、事件与取消等接口，可作为网关内的执行控制层。
网关把外部协议任务映射为隔离的 Codex 会话，并维护 Nacos Publication，即构成技术上
可实现的服务化路径。这是基于接口的设计推导，尚未证明 A2A 任务、审批与产物映射完整。
依据：[RAD 规范](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/rad-protocol-spec.md)、
[Codex app-server](https://learn.chatgpt.com/docs/app-server)、
[Codex SDK](https://learn.chatgpt.com/docs/codex-sdk)。

## 4. 页面与扩展入口

MCP Apps 把 UI 作为 MCP 服务暴露的资源，与工具关联。宿主读取页面，在隔离容器中运行，
通过桥接传递工具结果和页面请求。因此列表、搜索框、详情和操作按钮可以复用现有核心，
无需把整个 Nacos 控制台嵌入宿主。轻量页面可以是单个 HTML 产物；页面持久状态仍由核心
维护。依据：[MCP Apps UI 指南](https://developers.openai.com/plugins/build/chatgpt-ui)和
[官方 Quickstart](https://developers.openai.com/plugins/build/app-quickstart)。

截至 2026-10-19 的核对日期，需要区分标准能力、产品支持与本插件的可用性：

| 判断 | 证据与边界 |
| --- | --- |
| MCP Apps 能承载交互页面 | 官方 UI 指南给出 UI 资源、隔离页面和桥接工具调用机制；可以承载本设计的轻量视图。 |
| Codex 有交互式 MCP Apps 能力线索 | 官方 [Codex GovCloud 配置](https://learn.chatgpt.com/docs/enterprise/govcloud-configuration)列出 Interactive MCP apps 和 `enable_mcp_apps` 策略开关；这是能力存在的旁证，不是第三方本地插件的兼容保证。 |
| 官方 UI 教程不能直接证明 Codex 全部入口可用 | Quickstart 明确把 MCP 工具用于 ChatGPT/Codex，而 UI 示例的宿主写为 ChatGPT；不能据此推定本地 stdio MCP 的页面在 Codex 同样可用。 |
| 固定入口有独立的扩展机制 | [Extensions 文档](https://developers.openai.com/plugins/build/extensions)描述全局入口和会话侧面板；其页面与[平台支持表](https://github.com/openai/mcp-extensions/blob/main/docs/spec.md#platform-support)以 ChatGPT 产品面为范围，仍须逐项核对目标 Codex。 |
| 目标 Codex 可打开本地插件页面 | 独立探针已打开并完成回调；用户已确认重启后资源中心入口出现，并完成若干简单操作。完整流程、重开一致性及 UI 改版仍待逐项验收，不外推全部入口或版本。 |

设计结论是采用 MCP Apps 作为页面的优先技术方案，并将 Codex 实际兼容性列入 P0。
固定侧栏入口是页面渲染之外的能力，不能作为默认已支持项；只支持会话触发页面的宿主
也可以提供资源中心，但需要验证可重复进入的实际流程。当前不声明最低 Codex 版本。
CLI 等无页面宿主仍可使用相同工具，不承担图形页面交付。

## 5. 初始化和可选提醒

本地插件可在获准范围内读取 Skill 元数据和文件，维护清单、内容摘要及远端映射，因此
“已有资源盘点”和“变化后生成上传候选”不需要 Nacos 增加新的事件接口。目标环境必须
实际允许文件访问；云端插件不能据此获得用户本机资源。

| 机制 | 已有依据 | 能证明与不能证明的内容 |
| --- | --- | --- |
| 初始化工作流 | [插件打包文档](https://developers.openai.com/plugins/build/plugins#add-an-onboarding-skill)定义 `onboardingSkill`。 | 用户运行 setup 可进入配置与盘点；没有证明安装结束会自动扫描或弹窗。 |
| 宿主资源枚举 | [Skills 文档](https://learn.chatgpt.com/docs/build-skills)说明发现范围；[app-server](https://learn.chatgpt.com/docs/app-server)有 `skills/list` 和 `skills/changed`。 | 具备枚举/失效通知的技术基础；普通插件是否能接入宿主进程须验证，必要时在授权目录扫描。 |
| 工作流内提示 | 插件 Skill 可以组织创作、验证、候选检查和上传选择。 | 明确进入插件工作流后可串联步骤；仅安装插件不能确保其他 Skill 完成后必定调用它。 |
| 全局提醒增强 | [Hooks 文档](https://learn.chatgpt.com/docs/hooks)提供 `PostToolUse`、`Stop` 等事件。 | 可以在支持的工具路径内感知文件变化；事件不等于 Skill 创建完成，需防抖、校验与去重。 |
| Hook 可用性 | 同一 Hooks 文档要求非托管 Hook 获得信任；[打包文档](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks)限制插件 Hooks 的支持与发布渠道。 | 手动安装的 Codex 桌面插件有增强路径；安装不自动信任，含 Hooks 的包当前不具备官方公开目录提交资格。 |

基于这些接口的设计推导是：基础包通过初始化和插件工作流实现可控闭环，增强包用 Hooks
扩大独立 Skill Creator 调用的提醒覆盖。异步事件不自动开启空闲会话，未运行时也无法
保证持续监听；因此事件检测、提示可见与实际上传须分别验证。原设计阶段仅核对文档和接口，
当时未运行原型，也未扫描或上传用户已有资源；当前开发状态见 TODO，F17 仍未实施。

## 6. 适配验收

若后续启用 Hooks，`PostToolUse` 可为当前工作流提供简短候选上下文；使用 `Stop`
汇总待提醒项时，最多做一次受控继续，并检查已继续标志，避免反复阻止回合结束。
这些事件映射只属于 Codex 的候选方案，实际支持仍需按目标版本和分发渠道验证。

每个支持版本分别验证本地插件安装、工具发现、Skill 发现与真实使用、MCP 配置刷新，
以及声明支持的平台和执行位置。页面必须验证本地插件来源、transport、资源读取、
桥接、重开和入口形态；工具调用成功不能代替页面验收。

初始化入口与授权目录扫描独立验证。创建后提醒仍为可选研究，不因存在 Hook 接口而
视为已经实现；信任、关闭、覆盖、去重与分发渠道均须单独验证。
