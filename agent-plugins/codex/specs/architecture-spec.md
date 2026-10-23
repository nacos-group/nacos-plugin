<!-- Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 -->

# Codex 适配与实现规范

本文件补充[通用架构](../../specs/architecture-spec.md)，只记录 Codex 的接入和实现选择。
交付状态以 [TODO](TODO.md) 和[兼容说明](../docs/compatibility.md)为准。

## 1. 插件与资源加载

Codex 插件包含工作流 Skills 和本地 stdio MCP 入口，资源中心采用 MCP Apps。
全局导航和会话侧面板分别适配；页面入口、工具和对话交接映射见
[Codex UI 设计](resource-center-ui-spec.md)，具体版本的验证边界见[可行性分析](feasibility-spec.md)。

Skill 路径与配置文件由 `hosts/codex.py` 发现，具体默认值见 UI 规格。
资源身份、缓存归属、最小配置修改和加载证据遵循[通用装配契约](../../specs/assembly-sync-spec.md)；
不在本文件另定义一套安装、刷新或权限规则。

初始化入口为 `skills/setup/SKILL.md`。问答、非敏感预填、默认值保留和诊断顺序遵循
[通用初始化](../../specs/onboarding-spec.md)，工具映射见[初始化适配](credential-onboarding-spec.md)。
当前不提供 Hooks 或后台同步；可选 Hooks 的 Codex 研究记录保留在可行性分析中。

## 2. 当前实现选择

核心采用 Python 3.11+，直接适配固定版本的 HTTP 契约；PyYAML 使用安全解析模式，
锁定依赖并随 zipapp 交付。安装不要求 Maven、Node 或联网安装 Python 包。
本地 stdio MCP 与 CLI 复用核心；持久实现为带 schemaVersion 的私有 JSON 文件、进程锁
和原子替换，包快照与操作记录分离。计划、授权、并发及恢复语义遵循通用规范。

Nacos 认证当前支持原生 login/token 的环境变量引用、macOS 页面填写和明确选择的
无认证模式。页面采用[通用 MCP 加密信封方案](../../specs/credential-management-spec.md#6-可选的-mcp-加密信封方案)
及[macOS 存储实现](../../specs/platforms/macos-credential-store.md)，具体映射与平台限制见凭据适配。

下游 MCP 首批选择 Streamable HTTP，Agent 选择 A2A 0.3.0 JSON-RPC 的非流式
message/send、tasks/get、tasks/cancel；流式、OAuth 和其他协议暂不声明支持。
下游认证当前仍使用独立环境变量，实际兼容性按 TODO 的 P0/P1 验收。

## 3. AgentSpec profile（后续能力）

Codex profile 需遵循[通用装配契约](../../specs/assembly-sync-spec.md)，兼容 Nacos
现有的 `manifest.json` 与 `worker.suggested_name` 入口。schema、字段映射和完整样例
在 T05 独立定稿，不能把任意 AgentSpec 包直接视为 Codex 原生 Agent 定义。

## 4. 执行服务化（后续能力）

拟使用 Codex 官方支持的 SDK 或 app-server 接口创建和管理执行会话，通过本机受控进程
连接，由网关提供对外协议。会话启动/继续、事件、审批、取消和关闭需要按 Codex 接口验证。

身份隔离、控制入口保护、发现及运行活性遵循[Agent 互联规范](../../specs/agent-interoperability-spec.md)。
服务化属于 P3，不是当前消费插件的启动或安装依赖。

## 5. 源码布局

源码位于 `agent-plugins/codex/`。`plugin.json`、`mcp.json` 和 `skills/` 直接位于
该目录；`src/`、`tests/`、`scripts/`、`docs/` 与 `specs/` 分别保存实现、测试、构建、
使用说明和专属设计。`src/nacos_registry/hosts/codex.py` 是运行时配置适配模块。

通用契约在 `agent-plugins/specs/`，系统存储实现在其中的 `platforms/` 记录；
Codex 目录保留实现映射、视觉规格和验收结果。规范归属不决定共享源码必须放在哪里，
实际代码复用按通用架构记录来源与边界。
