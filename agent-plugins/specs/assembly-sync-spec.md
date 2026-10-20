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

# 装配与更新规范

本文约束 F04–F07、F10。装配是将已选择的远端资源转化为目标宿主能够使用的能力，
同时维护来源、依赖、版本和恢复记录。

## 1. 计划与应用

```text
解析引用 -> 读取确切版本 -> 校验包与依赖 -> 生成差异计划
         -> 检查授权与本地基线 -> 应用 -> 验证宿主加载 -> 保存结果
```

计划包含所有新增、修改、移除的文件与配置、依赖版本、所需服务认证及加载方式。
计划基于确切版本和本地摘要；应用前必须重新校验本地基线，变化后重新生成计划。
同一个 installation 的应用与卸载必须串行化，避免多个会话相互覆盖。

支持临时目录预校验、文件备份、操作日志和可恢复替换。多文件、多宿主配置或远端操作
不具有天然事务性；进程中断后根据日志恢复或报告部分应用，不能宣称跨系统原子提交。
重复应用相同计划在基线不变时应收敛到相同结果。

## 2. 依赖模型

依赖来自明确的包字段或插件约定的宿主 profile，不从自然语言正文猜测并自动安装。
每个依赖记录资源身份、版本选择器、必需/可选、用途和目标作用域；解析后锁定确切版本。

- 检查循环依赖、同名冲突、不可满足的版本约束和跨来源信任边界。
- 必需依赖不可用时不得将整体标为可使用；可选依赖缺失时明确列出能力缺口。
- 不支持隐式版本范围的类型，必须使用确切版本或服务端支持的路由选择器。
- 引入新来源、凭据、执行权限或新脚本属于计划变化，必须重新匹配授权策略。
- 锁定结果代表这次解析结果，不代表 Nacos 提供跨资源一致性快照。

## 3. Skill 装配

验证 SKILL.md、资源文件与引用完整性后，安装到适配器确认的项目或用户作用域。
远端包名、资源名和宿主 skill 名应分别记录；遇到重名不静默覆盖，也不随意重写技能内容。

安装记录保留全部受管文件及其基线摘要。插件包内置的工作流与用户从 Nacos 下载的 Skill
使用不同归属；远端资源更新不改写插件安装缓存。完成后验证宿主发现结果，未加载时明确
报告需要新会话、刷新或重启。更新不追溯修改已经进入旧会话的指令文本。

## 4. Prompt 装配

Prompt 按确切版本读取，对变量执行声明的类型和必填校验。缺少输入时询问必要信息，
不编造业务参数。渲染只执行已支持的占位符规则，不执行模板中的任意代码。

通过宿主支持的任务输入或模板入口使用结果，保留来源和版本。远端 Prompt 不获得高于
宿主、组织策略和用户意图的指令优先级。一次任务使用一个明确版本快照；更新默认影响
后续任务，不静默替换正在执行任务的上下文。

## 5. AgentSpec 装配

AgentSpec 是 manifest 与资源文件组成的版本包。适配器只解释明确声明且支持的模板 profile，
先产生能力映射，再转化为 Skill、Prompt、MCP 连接或其他被宿主支持的资源。

| 输入类别 | 处理规则 |
| --- | --- |
| 指令或说明文件 | 按 profile 映射到宿主支持的任务/技能入口，保留内容来源。 |
| 资源依赖 | 进入依赖图，使用统一版本解析与授权流程。 |
| 宿主设置 | 仅映射支持且已授权的设置，不接管宿主全局安全策略。 |
| Dockerfile、cron 或脚本 | 作为资源保留；安装模板不等于执行或启用这些内容。 |
| 不支持的必需字段 | 阻止应用，给出具体缺口；可选字段的忽略必须在计划中可见。 |

当前 Nacos 包解析要求 `manifest.json` 中的 `worker.suggested_name` 作为资源名称来源。
各应用的模板 profile 必须兼容既有包入口；profile 的 schema、字段与映射需在实施前独立定稿，
不得在本草案中假定 Nacos 已接受另一种宿主原生 manifest。通用模板和宿主生成物分别保存，
不能把转换后的文件反向覆盖为远端源包。

## 6. MCP 装配

取得 Nacos 的服务定义和当前可用 Endpoint 后，核验 transport、宿主支持、目标地址、
服务认证、可用工具及策略。Nacos 登记的后台 HTTP 服务不必然是可直接调用的 MCP Endpoint；
需要协议转换的服务必须连接实际网关提供的 MCP 前端地址。

固定基线中，原生 `mcp-streamable` 服务的直连地址位于 `backendEndpoints`，并不要求
存在 `frontendEndpoints`；普通 `http` 后端只有明确的 MCP 前端才能消费。两种情况分别
适配，HTTP/HTTPS scheme 必须由端点元数据明确提供，缺失时返回不支持而不猜测。

| 模式 | 连接关系 | 更新边界 |
| --- | --- | --- |
| 宿主原生连接 | 插件维护受管配置，宿主直接连接目标 MCP。 | 地址或工具变化是否热加载由宿主能力决定。 |
| 显式代理连接 | 宿主连接稳定代理，由代理发现并连接下游 MCP。 | 代理可更新下游，但必须处理 schema、认证、会话和工具策略变化。 |

两种模式必须明确选择。代理不得将所有下游调用折叠成绕过宿主工具策略的无限制入口；
需保留服务/工具身份、参数 schema、权限与审计。宿主不支持工具列表动态变化时，代理也
必须返回待重新加载状态，不能承诺透明热更新。

本地 stdio 服务意味着执行本地程序；注册信息本身不构成执行授权。程序来源、固定版本、
启动参数和环境变量引用必须出现在计划中。凭据按目标服务绑定，不能从 Nacos metadata
中提取秘密并自动分发。连接成功后还需验证工具发现，不默认调用有副作用的业务工具。

## 7. 更新策略与触发

| 策略 | 行为 |
| --- | --- |
| 固定版本 | 保持锁定版本，只有显式变更才升级。 |
| 发现更新 | 检测变化并生成计划，由用户按已有授权应用。 |
| 受控自动更新 | 在可信来源、作用域、版本路由和允许的变更范围内自动应用。 |

检测触发包括显式同步、资源使用前检查，以及有明确进程所有者的后台轮询/Watch。
Skill 与 AgentSpec 使用各自的 MD5 条件查询，Prompt 使用其独立契约；Agent Watch 返回
变化提示后必须重新 Discover。MCP 按已验证的接口/SDK 语义刷新，不假定所有资源共享推送。
服务端 MD5 用于条件读取，本地文件基线使用内容摘要；不得混淆摘要用途或仅凭摘要建立来源信任。

轮询有上限、退避和取消，不允许慢响应导致任务堆积。宿主退出后本地插件进程停止时应明确
表示同步已停止；持续后台运行属于独立服务部署，不能只依靠 Skill 的自然语言指令。

## 8. 冲突、不可用与恢复

| 事件 | 行为 |
| --- | --- |
| 远端变化，本地未改 | 按策略生成或应用新计划，保存上一个成功版本。 |
| 本地变化，远端未改 | 保留本地修改；发布需走独立的资源开发流程。 |
| 两侧均变化 | 基于安装基线比较，停止自动覆盖，产生冲突计划。 |
| 连接失败 | 保留诊断和最后成功记录，按授权的离线策略决定是否继续使用。 |
| 明确撤权、禁用或缺失 | 淘汰活动缓存并停止插件自动使用，按宿主能力禁用受管入口。 |
| 应用或加载失败 | 恢复可恢复的受管修改，报告未完成步骤和实际生效版本。 |
| 回滚 | 校验目标仍符合当前授权与可用策略，再恢复本地快照；不回滚远端发布事实。 |

卸载只移除仍由插件拥有且未被修改的内容。用户修改的文件、共享依赖和无归属配置保留并
报告。依赖只有在无其他 installation 使用时才可清理。已经进入会话或被用户复制的内容
不属于可保证撤回的范围。

## 9. 验收重点

覆盖依赖循环、重名、多会话并发、计划过期、ZIP 越界、文件修改冲突、部分写入恢复、
模板字段不支持、MCP 独立认证、工具 schema 变化、后台取消，以及装配成功但宿主尚未加载。

规范依据：[Skill](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/skill-spec.md)、[Prompt](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/prompt-spec.md)、
[AgentSpec](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/agentspec-spec.md)、[MCP](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/mcp-server-spec.md)、
[Agent API](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/agent-api-spec.md)。
