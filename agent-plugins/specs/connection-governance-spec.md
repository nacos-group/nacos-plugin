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

# 接入与治理规范

本文约束 F01、F11，并为 F02–F10 的操作提供连接、身份和授权边界。

## 1. 连接配置

一个连接 profile 表示一个可识别的 Nacos 入口。配置至少包含稳定 profile ID、展示名、
服务端 base URL（保留 scheme 和 context path）、默认 namespace、认证方式和凭据引用。
Client 与 Admin 入口存在部署差异时必须显式配置，不能把 Console 地址推测为 Client 地址。

个人可维护多个 profile；企业可以分发不含秘密的入口配置及策略。用户选择业务环境时应看到
易懂的环境名称，写入和发布结果必须包含实际 profile 与 namespace，避免混用生产和测试环境。
企业入口模板、策略下发的具体载体由部署方式决定，不视为 Nacos 已有的新 API。

## 2. 初始化与诊断

| 步骤 | 行为 | 成功证据 |
| --- | --- | --- |
| 配置入口 | 选择个人或企业入口，检查 URL、namespace 和执行环境。 | 配置可解析且来源可信。 |
| 建立身份 | 通过支持的本地凭据存储或认证流程获取身份。 | 目标服务接受该身份。 |
| 判断能力 | 读取能力信息并结合已知 API 契约判断可执行操作。 | 保存支持、不支持、未知三态。 |
| 验证资源访问 | 在授权范围内做只读查询，区分空结果和访问失败。 | 当前身份能访问所选环境。 |
| 保存结果 | 保存配置与诊断状态，向用户给出可用能力和后续动作。 | 不以“配置文件已保存”替代连通成功。 |

不得通过创建资源或发布地址来探测连接。能力缓存按实际 URL、执行环境和身份摘要隔离，
身份切换时不得复用原身份的资源缓存。

Nacos 的 Client HTTP capabilities 只声明响应节点的实现能力，不代表资源权限、管理面
能力、全群集就绪或迁移完成。缺失字段、404/405 和非法响应均可能表示未知；鉴权失败和
网络故障必须保留原分类，不得将其解释为可以自动切换旧协议。

初始化还应提供本地资源盘点与托管选择，具体流程见[本地资源托管](local-resource-onboarding-spec.md)。
扫描、上传草稿与发布是不同授权范围，用户可跳过盘点而直接使用远端资源。

配置中的“权限”表示真实身份与本地允许的操作范围：消费身份可搜索/读取资源，开发身份
按服务端授权上传/发布 Skill；下游 MCP/Agent 凭据另行绑定。插件可以限制可执行操作，
不能通过本地开关授予服务端权限，或要求全部使用者配置管理员账号。

## 3. 凭据与身份边界

- 认证适配器按支持矩阵接入 Nacos 原生认证或部署方采用的认证方式；不默认声称支持全部插件。
- 配置和发布包只保存凭据引用。凭据通过宿主支持的安全入口或受保护的本地存储输入，
  不要求员工在普通对话、资源描述或共享配置中填写秘密。
- Nacos 身份、MCP 服务身份、远端 Agent 身份和网关入站身份分别管理；Nacos token
  不能自动发送给发现到的其他服务，重定向也不能携带跨来源秘密。
- 登录过期可以执行受支持的刷新流程；撤权和身份拒绝不能通过换用管理员身份自动绕过。
- 同一 profile 的个人登录态不能因企业共享插件而共享给其他员工。

## 4. 企业资源治理

企业管理员负责把资源发布到正确环境，并通过 Nacos 的权限、可见性与发布流水线进行治理。
插件展示真实的 owner、来源、版本和可用性，不另建可绕过 Nacos 的资源授权数据库。

| 控制层 | 决定内容 |
| --- | --- |
| Nacos | 对资源的查询、发布、版本操作和可见性授权。 |
| 远端服务 | 对实际 Agent/MCP 调用和数据访问的授权。 |
| 企业插件策略 | 允许的入口、资源来源、更新渠道、操作范围和执行目标。 |
| 宿主 | 文件访问、工具执行、网络访问及审批能力。 |
| 用户授权 | 本次任务或持久策略下允许的具体操作和作用域。 |

执行条件是各层约束的交集。用户偏好可以进一步收紧，不能扩大组织或宿主策略；来源内容
不能授予权限。组织策略必须由可验证的管理渠道提供，普通资源中的同名字段不具备管理权限。
远端内容只作为资源输入，不能修改这些信任边界。

资源 scope 的 PUBLIC/PRIVATE 遵循 Nacos 的可见性含义，不等价于向互联网公开发布。
企业入口共享、资源授权、宿主插件安装和远端服务授权是不同动作，必须分别核验。

## 5. 员工使用流程

1. 员工选择已配置的企业入口并表达业务目标。
2. Agent 查询当前身份可见的资源，以业务用途、来源和必要输入解释候选项。
3. 对明显匹配且已有授权的资源自动准备；存在用途或目标歧义时才要求选择。
4. 插件完成依赖解析和使用准备，必要的认证或额外操作通过宿主原生交互完成。
5. 返回任务结果；遇到拒绝时提供可操作的申请或联系入口，不泄漏无权访问资源的细节。

自然语言匹配由宿主 Agent 结合 Nacos 搜索完成，不要求服务端必须配置向量检索。
管理员配置只需提供员工完成任务必需的信息，诊断细节可以另行查看。

## 6. 发布与撤权

上传草稿、提交审核、上线、修改可见性和删除是独立行为，授权必须涵盖实际副作用。
没有匹配 Pipeline 的 submit 可能直接上线；界面和工具描述不能将其固定描述成“只送审”。
已授权的批量工作流可以连续执行，但必须逐项保存目标版本及真实结果。
发布计划必须呈现目标可见性；创建时的默认 scope 由服务端决定，不能假设企业资源默认
PRIVATE。需要修改 scope 时使用对应管理操作，并将其实际结果纳入发布核验。

收到明确撤权、禁用、下线或资源缺失证据时，应停止插件后续自动装配和调用，清理活动缓存，
并将托管安装标记为不可用；支持卸载或禁用的宿主应撤销托管入口。备份、用户复制的内容和
已经进入会话的文本无法保证远程抹除，产品不能宣称强制召回已经交付的知识。

离线使用必须由企业策略和资源类别显式允许，并具有有效期限；不默认对全部资源永久缓存。
暂时连接失败可以保留上一次成功版本供诊断或授权的离线使用，不能伪造服务端最新状态。

## 7. 验收重点

需要覆盖多 profile 同名资源隔离、身份切换、空目录、token 过期、权限拒绝、发布后可见性、
下游独立认证、可信策略与资源内容区分，以及普通员工无需管理权限即可发现并消费资源的路径。

规范依据：[AI Registry](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/ai-registry-spec.md)、
[鉴权与权限](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/auth/auth-permission-spec.md)、
[可见性](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/auth/visibility-plugin-spec.md)、
[AI 资源生命周期](https://github.com/alibaba/nacos/blob/1511b5a85f744acb0ad54e8213b1f4d82674799c/specs/zh-cn/ai/ai-resource-lifecycle-spec.md)。
