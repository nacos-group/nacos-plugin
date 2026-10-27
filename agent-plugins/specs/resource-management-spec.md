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

# 资源管理规范

本文约束 F02、F03，覆盖资源发现、版本读取以及 Skill、Prompt、AgentSpec 的开发与发布。
Agent 定义和运行地址的区别见[Agent 互联](agent-interoperability-spec.md)。本地创作来源、
首次盘点和上传提醒见[本地资源托管](local-resource-onboarding-spec.md)。

## 1. API 分工

| 工作 | 接口选择与规则 |
| --- | --- |
| 消费者搜索 | 优先使用 Client 统一资源搜索或类型专用搜索；保留可见性与分页契约。 |
| 获取已知资源 | 使用对应 Client API，根据版本选择器解析可消费内容。 |
| 开发和治理 | 使用 Admin API，处理草稿、审核、发布与版本状态。 |
| 已有 CLI/SDK 复用 | 只使用版本和结构化输出已确认的命令/方法，保持相同业务契约。 |

代码基线中的主要 Client 入口为 `/v3/client/ai/resources/search`、
`/skills`、`/prompt`、`/agentspecs`、`/mcp` 和 `/agents`（后五项相对
`/v3/client/ai`）。每个入口的参数名、响应格式和条件查询规则必须分别适配。
base URL 的 context path 由连接配置提供，不写死额外的 `/nacos`。

## 2. 搜索与选择

普通需求如何触发搜索、默认搜索预算与后续类型流程交接见
[按任务意图发现能力](capability-discovery-spec.md)。搜索 API 可用不等于应用已实现隐式发现。

搜索输入至少支持当前入口、namespace、自然语言意图或关键词、资源类型和业务标签。
插件必须保留 Nacos 提供的 opaque cursor 或类型专用分页语义；不得把多个已分页的类型结果
拼接后声称是统一相关度、total 或全局排序。

候选项包含业务名称、用途、资源类型、来源和可获得的版本信息。选择后必须通过资源读取或
Discover 重新核验，搜索索引只用于发现，不是内容、权限、当前可用端点的最终事实来源。
发布后的索引存在收敛窗口；写入验收使用精确资源读取，不能因为搜索暂未命中而重复创建。

跨 profile 搜索必须分来源标识结果，不能混用授权或用不透明 cursor 跨入口翻页。
没有匹配项时可以解释结果和当前查询范围，不能自动转到未授权公网 registry。

## 3. 版本选择

插件统一接受确切 version、label 或资源默认版本三种选择意图，但每次请求只发送一种选择。
具体资源不支持的选择器必须明确拒绝或通过已授权的版本解析流程处理，不能向 API 发送
猜测参数。例如当前 MCP Client 查询使用确切 version 或 latest，不能假定支持所有 label。

解析后记录确切版本与内容摘要。不可假设所有资源版本都遵循 SemVer，版本顺序与 label
指向遵循服务端规则。`latest` 由 Nacos 管理，不由插件通过标签写入强行改写。
消费默认只接受服务端允许读取的在线资源；开发者读取草稿使用管理面并明确展示其状态。

## 4. 资源开发输入

| 类型 | 输入 | 发布前检查 |
| --- | --- | --- |
| Skill | SKILL.md、引用文件和资源元数据。 | frontmatter、包边界、引用完整性、名称和版本目标。 |
| Prompt | 模板内容、变量定义与描述。 | 必填变量、变量格式、资源身份、目标草稿。 |
| AgentSpec | manifest.json 与资源文件。 | manifest 身份、引用文件、所声明的宿主 profile 和依赖。 |

对用户已有目录先读取差异与发布基线，再决定创建新资源、新版本或更新草稿。
已发布版本的内容不能通过本地覆盖操作隐式修改。针对 Nacos 现有草稿接口，必须读取当前
working draft 和目标版本，避免将另一个开发者的工作当作自己的可覆盖内容。

Skill 上传必须适配[Skill 规范](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/skill-spec.md)的预检结果：草稿已存在、审核中、
无权限、版本调整等状态不能按普通成功处理。预检接收 ZIP，属于内容上行，须在上传范围
已获授权后执行；其目标版本是推算值，上传后的真实版本必须重新核验。上传草稿与发布
是独立动作，不能以“自动托管”为由默认继续 submit。

## 5. 发布状态与结果

插件遵循 Nacos 的类型化生命周期，不引入第二套“发布成功”状态：

```text
create / upload draft -> edit -> submit
                               -> reviewing -> reviewed -> publish -> online
                               -> online（无匹配 Pipeline 时按服务端行为）
```

`reviewed` 表示审核完成，必须继续检查审核结果；不能仅凭该状态认定通过。
拒绝后的编辑、重新提交、上线/下线等操作使用对应的现有 API。强制发布不是普通自动化的
默认回退路径，不在审核失败时自动调用。

一次发布应返回资源身份、确切版本、当前状态和下一步。响应丢失时先读取确切目标并核对
内容/状态；未确认幂等的新增操作不得盲目重试。Nacos 不提供 CAS 的写入，插件只能进行
基线重读和冲突提示，不能宣称消除了跨客户端并发覆盖窗口。

多资源发布按依赖顺序逐项执行，记录每个版本的状态。Nacos API 未提供跨资源事务，
中途失败必须报告部分成功；不能通过静默下线或删除已发布资源伪装事务回滚。

## 6. 内容边界与诊断

对 ZIP 必须检查路径穿越、绝对路径、符号链接、展开体积、文件数量及引用完整性，
只访问本次操作授权的目录。校验不会运行包内脚本。未知字段需要按对应包规范保留或报错，
不能为了上传成功静默删除资源内容。

工具错误必须区分校验、鉴权、可见性、版本冲突、审核拒绝、超时和服务端能力不足。
原始错误码可以保留在诊断中，但日常用户看到的是操作结果和处理建议。
日志以资源身份、版本、操作 ID 和摘要为主，不记录秘密或全部包内容。

## 7. 验收重点

验证搜索分页、相同名称跨入口隔离、索引延迟、版本/label 解析、草稿覆盖冲突、
Pipeline 通过/拒绝、无 Pipeline 直接上线、发布响应丢失和批量部分成功。
下载或消费侧必须确认确切目标版本，而不仅是“搜索到了同名资源”。

规范依据：[资源检索](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/ai-resource-search-spec.md)、
[资源生命周期](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/ai-resource-lifecycle-spec.md)、
[Skill](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/skill-spec.md)、[Prompt](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/prompt-spec.md)、
[AgentSpec](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/agentspec-spec.md)。
