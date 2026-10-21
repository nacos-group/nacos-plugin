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

# Codex 适配与实现规范

本文件补充[通用架构](../../specs/architecture-spec.md)，只记录 Codex 的接入和实现选择。
交付状态以 [TODO](TODO.md) 和[兼容说明](../docs/compatibility.md)为准。

## 1. 插件与资源加载

Codex 插件包含工作流 Skills 和本地 stdio MCP 入口。MCP 入口向模型提供确定性的操作，
共享核心完成实际同步。资源中心采用 MCP Apps 作为页面方案；全局导航和会话侧面板
作为独立宿主能力验证后启用。页面与自然语言入口复用同一工具和操作状态，详见
[通用 UI 交互](../../specs/resource-center-ui-spec.md)与[Codex UI 设计](resource-center-ui-spec.md)。
官方 UI 文档与具体 Codex 版本的支持范围
不能直接等同，验证边界见[可行性分析](feasibility-spec.md)。

- 本地 Skills 使用目标 Codex 版本支持的项目或用户目录；安装位置由适配器发现和选择，
  不把 nacos-cli 默认下载目录视为宿主已经加载的位置。
- 插件内置 Skills 随插件包升级；从 Nacos 下载的用户资源存放在单独的托管位置，
  不改写 Codex 的插件安装缓存。
- MCP 首先使用宿主原生连接方式；动态代理作为显式运行模式，见[装配与更新](../../specs/assembly-sync-spec.md)。
- 配置变更通过解析后的最小修改保留其他配置；不得重写整个配置文件或覆盖用户工具策略。
- 热加载、新会话加载和重启是不同能力。适配器必须读取或验证当前加载结果，
  仅有配置文件写入成功时返回“待加载”。
- 不能直接访问本机的宿主使用远端接入部署方式；该方式不能承诺本地文件装配能力。

初始化使用已验证的 onboarding skill 入口。资源盘点与候选提醒由本地核心维护，可选
Hooks 仅提供事件输入；安装插件不等于 Hooks 已获信任，也不等于存在全局 Skill 创建事件。
详见[本地资源托管](../../specs/local-resource-onboarding-spec.md)。

Codex 是具体适配器，不能把整个产品的资源模型限定为 Codex plugin manifest。
其他 coding agent 和 personal agent 的名称与支持版本在实现验证后加入矩阵。

## 2. 当前实现选择

共享核心采用 Python 3.11+，直接适配固定版本的 HTTP 契约；PyYAML 使用安全解析模式，
锁定依赖并随 zipapp 交付。运行时单独声明，安装不要求 Maven、Node 或联网安装 Python 包。
本地 stdio MCP 与 CLI 复用核心；状态使用带 schemaVersion 的私有 JSON 文件、进程锁和
原子替换，包快照与操作记录分离。每次修改先创建有版本、基线、作用域与副作用的计划，
再显式应用；无服务端 CAS 时仍保留并发窗口说明。首期没有 Hooks 或后台同步进程。

Nacos 认证首批实现原生 login/token 环境变量引用，以及明确配置的无认证模式；Client 和
Admin 身份独立。下游 MCP 首批选择 Streamable HTTP，Agent 选择 A2A 0.3.0 JSON-RPC
的非流式 message/send、tasks/get、tasks/cancel；流式、OAuth 和其他协议暂不声明支持。
这些是实现选择，实际兼容性仍按 TODO 中的 P0/P1 验收，不把模拟端点等同于真实服务验收。

## 3. AgentSpec profile（后续能力）

Codex profile 需遵循[通用装配契约](../../specs/assembly-sync-spec.md)，兼容 Nacos
现有的 `manifest.json` 与 `worker.suggested_name` 入口。schema、字段映射和完整样例
在 T05 独立定稿，不能把任意 AgentSpec 包直接视为 Codex 原生 Agent 定义。

## 4. 执行服务化（后续能力）

使用 Codex 官方支持的 SDK 或 app-server 接口创建和管理执行会话，优先通过本机受控
进程连接，由网关提供对外协议。不得将未经保护的宿主控制端口直接暴露为公共 Agent 服务。

执行适配必须验证会话启动/继续、事件流、审批、取消和关闭的实际行为；模型访问权限与
调用额度使用部署方合法配置的账号或服务身份。个人桌面会话与网关会话分别管理，
不默认复用个人的所有项目权限。

服务发现、身份隔离与运行活性遵循[Agent 互联规范](../../specs/agent-interoperability-spec.md)。
服务化属于 P3，不是当前消费插件的启动或安装依赖。

## 5. 源码布局

源码位于 `agent-plugins/codex/`。`plugin.json`、`mcp.json` 和 `skills/` 直接位于
该目录；`src/`、`tests/`、`scripts/`、`docs/` 与 `specs/` 分别保存实现、测试、构建、
使用说明和专属设计。`src/nacos_registry/hosts/codex.py` 是运行时配置适配模块。

通用规范维护在 `agent-plugins/specs/`。未来新增 Agent 应用时，在 `agent-plugins/`
下增加同级目录；通用资源模型不依赖某种 manifest 或配置语法。当前代码随 Codex 组件
交付，后续若实际复用实现，再提取公共代码，避免各适配目录复制后各自演进。
