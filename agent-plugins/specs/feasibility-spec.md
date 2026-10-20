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

# 通用可行性分析

本文只解释方案成立的技术原理、依据和验证边界。产品目的见 [Overview](README.md)，
功能契约见[功能规范](functional-spec.md)，阶段安排见 [TODO](TODO.md)。

| 分析基线 | 值 |
| --- | --- |
| 核对日期 | 2026-10-19 |
| Nacos 代码 | upstream/develop，1511b5a85f744acb0ad54e8213b1f4d82674799c。 |
| 代码版本 | pom revision 为 3.3.0-RC；不能外推所有旧版本具备同等能力。 |
| 本文证据范围 | 原设计阶段的规范、Controller、包解析实现静态核对；实现进展另见 TODO。 |
| 原设计阶段尚无证据 | 当时未进行插件运行、集成、性能和多宿主测试；此处保留历史分析，不代表当前实现状态。 |

## 1. 插件入口为何能够承载接入

宿主插件能够组合工作流指令与确定性工具入口：指令承担任务识别和工具选择，MCP 服务
承担协议调用与状态维护。本地 MCP 进程运行在用户工作环境中，因此可以在该环境的权限
和网络条件下接入内网服务、处理本地文件。纯云端入口能否访问内网或本机，需要另有
部署和连接能力，不能从“支持插件”推导出来。

各应用的插件入口和安装机制在其专属规范中核对，当前可参考
[Codex 可行性分析](../codex/specs/feasibility-spec.md)；不能由某一应用的插件支持推断其他应用的能力。

## 2. 接入 Nacos 为何无需重建资源服务

Nacos 已通过 Client 和 Admin HTTP 接口分离消费与管理，并维护统一资源身份、版本和
生命周期。外部工具可以作为 HTTP 调用方复用这些契约，不需要把插件作为 Java SPI
装入 Nacos Server，也不需要直接写 Config 或数据库。

| 原理证据 | 代码或规范入口 |
| --- | --- |
| 统一资源检索 | [检索规范](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/ai-resource-search-spec.md)，Client search facade。 |
| Skill 包读取 | [SkillClientController](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/ai/src/main/java/com/alibaba/nacos/ai/controller/SkillClientController.java)。 |
| Prompt 条件读取 | [PromptClientController](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/ai/src/main/java/com/alibaba/nacos/ai/controller/PromptClientController.java)。 |
| AgentSpec 读取与搜索 | [AgentSpecClientController](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/ai/src/main/java/com/alibaba/nacos/ai/controller/AgentSpecClientController.java)。 |
| MCP HTTP 查询 | [McpClientController](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/ai/src/main/java/com/alibaba/nacos/ai/controller/McpClientController.java)。 |
| Agent 发现与注册 | [AgentClientController](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/ai/src/main/java/com/alibaba/nacos/ai/controller/AgentClientController.java)。 |
| 版本与发布状态 | [生命周期规范](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/ai-resource-lifecycle-spec.md)及各资源 Admin Controller。 |

官方 [Client API](https://nacos.io/en/docs/next/manual/user/open-api/) 与
[Admin API](https://nacos.io/en/docs/next/manual/admin/admin-api/)可用于外部契约核对。
`next` 文档会演进，实际实现必须锁定测试过的服务端版本，并区分能力缺失、权限拒绝与
网络不通。现有 [nacos-skill-registry](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/skills/nacos-skill-registry/SKILL.md)
证明已有 CLI 工作流可参考，但它本身不证明完整插件能力。

## 3. 自动更新为何可以实现

资源读取支持确切版本及条件查询，部分资源提供 Watch，因此本地组件可以比较远端解析
结果与已安装基线，再执行增量变更。依赖锁定、文件摘要和操作日志属于插件自身可以维护
的状态，不要求服务端提供跨宿主文件事务。

条件查询只能证明资源内容状态，不证明应用已经重新加载。资源内容更新、配置刷新和
当前会话生效必须分别验证；无法直接承诺所有能力在当前会话无缝热更新。
依据：[Skill 监听契约](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/skill-spec.md)。

## 4. 模板适配为何需要显式映射

Nacos 保存版本化包，宿主负责解释包中的可执行含义。这种分工允许同一个 registry
保存面向不同宿主的模板，但不能保证它们共享同一套字段语义。

当前 [AgentSpecZipParser](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/ai/src/main/java/com/alibaba/nacos/ai/utils/AgentSpecZipParser.java)
从 manifest 的 `worker.suggested_name` 提取资源名，资源模型还可以包含 config、skill、cron
等内容。这说明读取包的能力已存在，也说明不能将任意包直接视为 目标应用的原生 Agent 定义。
采用有版本的宿主 profile、显式字段映射和不支持项校验，可以在不改变 Nacos 身份契约的
前提下完成适配；具体 profile 仍需样例与宿主验证。

## 5. Agent 双向互联为何需要调用层

RAD 返回协议描述和当前地址，不代理任务执行。因此消费方向需要协议客户端，提供方向
需要真正运行的 Agent 服务入口。注册中心与调用层分离，允许不同宿主通过同一发现协议
互联，但注册成功本身不能证明端到端成功。

如果目标应用提供受支持的会话创建、执行、事件和取消 API，网关可将外部协议任务映射
为隔离会话，再维护 Nacos Publication。具体执行 API、审批和产物映射由各应用单独验证。
依据：[RAD 规范](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/rad-protocol-spec.md)。

## 6. 分发为何与服务运行分开

插件是描述组件与运行入口的版本化包，源码可以构建该包；marketplace 或账户记录负责
发现和安装，并不会替使用者部署本地程序或提供 Nacos 访问权限。因此源码公开、包分发、
运行可用和公开目录上架应分别验收。平台准入规则详见[打包与分发](distribution-spec.md)，
其变化不影响 HTTP/MCP 适配的基本原理。

## 7. 页面与核心为何能够分离

页面负责列表、搜索、详情和操作计划展示，读写调用与对话复用同一核心及操作状态。
应用若支持 MCP Apps 或其他受支持的页面桥接，可由该桥接承载视图；具体 UI 资源格式、
展示模式、会话上下文和重新进入方式由应用适配验证。可行路径不等于已经交付页面。

固定导航和会话侧面板是独立能力；无图形能力的环境继续使用相同的工具入口。
具体产品支持和文档证据放在各应用的可行性分析中，不作为通用兼容承诺。

## 8. 初始化与本地盘点为何能够实现

本地组件可以在授权范围内读取资源元数据，维护清单、摘要和远端映射，因此首次盘点
不需要 Nacos 新增事件接口。目标环境必须实际允许文件访问；云端入口不能据此访问本机。

初始化通过各应用已验证的显式入口触发；有资源枚举 API 时核对其插件可用性，否则对
选定目录做有界扫描。工作流提示、全局事件和后台监听是不同能力，需分别验证触发范围、
交付时机和关闭方式。安装插件本身不构成扫描、上传或发布授权。

创建/修改后提醒的通用设计见[本地资源托管](local-resource-onboarding-spec.md)，是否实施
由各应用评估；具体事件名称、信任机制和目录准入规则维护在对应应用规范中。

## 9. 需要实证的假设

| 假设 | 验证方式 | 失败后的设计处理 |
| --- | --- | --- |
| 目标宿主能加载本地插件及 MCP | 干净环境安装，完成工具发现与只读调用。 | 调整宿主适配或限定支持矩阵。 |
| 目标应用可承载插件页面 | 锁定宿主版本/安装方式/transport，验证页面读取、初始化、工具回调、重开及策略关闭；全局/会话入口单独验证。 | 调整目标版本或入口；无法内嵌时明确延期，外部页面另作设计。 |
| 初始化及已启用的可选提示按声明触发 | 验证显式初始化、限范围盘点、已启用的工作流/事件入口、中断、忽略与去重。 | 保留插件工作流与按需补查，缩小自动提醒的覆盖承诺。 |
| 本地资源能够按声明方式刷新 | 分别改变 Skill、模板与 MCP 配置，观察新旧会话。 | 标记待加载，采用已验证的刷新/重启流程。 |
| 目标 Nacos 具备所需契约 | 对锁定版本执行认证、读取、发布及条件查询验证。 | 显式能力降级，必要时定义最低版本。 |
| AgentSpec profile 能够无歧义转换 | 使用真实包验证必需字段、依赖与宿主生成物。 | 缩小 profile 支持范围或独立修订设计。 |
| Agent 调用协议可完成任务闭环 | 验证普通、流式、失败、取消和审批等待路径。 | 明确协议子集，保留不可支持的状态。 |
| 打包产物可脱离开发机运行 | 在声明平台上从发布包安装并升级。 | 调整运行依赖或分平台交付。 |

当前可行性结论是：接入、版本管理、宿主装配和服务化均有明确接口基础与实现路径；
宿主生效、模板映射和双向任务协议仍须实测后才能转为兼容承诺。页面也有标准与扩展
机制可复用，但各应用中的 UI 加载和入口形态仍须独立验证。
