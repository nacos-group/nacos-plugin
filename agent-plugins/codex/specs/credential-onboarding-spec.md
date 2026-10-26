<!-- Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 -->

# Codex 初始化与页面凭据适配

本文件只记录 Codex 的入口、工具、运行限制与验证状态。用户流程、默认值和交接规则统一
见[初始化规范](../../specs/onboarding-spec.md)，输入与存储生命周期见
[凭据管理](../../specs/credential-management-spec.md)，系统实现见
[macOS 钥匙串](../../specs/platforms/macos-credential-store.md)。

## 1. 入口与工具映射

| 通用能力 | Codex 适配 |
| --- | --- |
| 本机初始化入口 | 插件内置 `skills/setup/SKILL.md`，从可访问本机的 Codex 对话执行。 |
| 运行工具与已保存状态 | `nacos_status`；读取当前配置、上下文、凭据状态及 `defaults`。 |
| 默认值发现 | `hosts/codex.py`；具体目录、标识和配置文件映射见 [4.5 设置](resource-center-ui-spec.md#45-设置)。 |
| 打开并预填设置 | `nacos_open_center_panel` 接受设置路由及非敏感草稿，打开当前对话的资源中心侧栏；无参数仍打开资源中心。 |
| 页面定位 | 资源中心 → 设置 → 连接与认证；根据已选认证定位用户名/密码或 Token 字段。 |
| 消费连接诊断 | `nacos_diagnose`；按通用流程确认保存后在既有授权内调用。 |
| 后续技能盘点 | `nacos_scan`、`nacos_select`、`nacos_onboarding`，遵循通用 F16 与 UIX-10。 |

Codex 云端会话缺少本机工具时，引导用户到桌面端的本地执行对话选择本插件继续；
不能把安装卡片或已读取 setup Skill 作为本地 MCP 已加载的证据。
侧栏能力不可用时给出实际错误及已验证的资源中心设置入口。全局页与当前对话侧栏的
具体入口判断见 [UI 适配](resource-center-ui-spec.md#2-两种入口一套工作区)。

## 2. 页面桥接与传输

Codex 采用[通用凭据规范第 6 节](../../specs/credential-management-spec.md#6-可选的-mcp-加密信封方案)
的 MCP 加密信封方案。算法、时效、限额、单次消费与失败行为以该方案为准。

| 环节 | Codex 映射 |
| --- | --- |
| 开始提交 | app-only `nacos_credentials_begin`；普通结果仅就绪状态，公钥、一次性会话标识、有效期放在 `_meta`。 |
| 页面加密 | WebCrypto；信封明文结构为 `{profile, changes}`。 |
| 提交密文 | app-only `nacos_credentials_save`；接收密文信封及配置上下文。 |
| 本机处理 | `credential_channel.py`、`credential_crypto.py` 与 `credential_service.py`。 |
| 持久存储 | `credentials.py` 的 macOS Keychain 适配；条目按本插件状态空间隔离。 |
| 页面状态 | 设置模型保留非敏感草稿与返回来源；保存后清空秘密，状态查询不返回秘密。 |

dev.13 的页面直连回环 HTTP 被实际 Codex CSP 拒绝。dev.14 已移除此服务，
页面不使用 `fetch` 提交凭据，UI 资源不声明本机 `connectDomains`。
`visibility: ["app"]` 只限制工具入口，不能替代通用规范要求的明文边界。

Codex/OpenAI 的普通结构化设置不作为凭据保险箱。桥接依据见
[MCP Apps 工具可见性](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx#visibility)
与[OpenAI 结构化设置](https://github.com/openai/mcp-extensions/blob/main/docs/spec.md#structured-settings)；
这些接口依据不构成所有 Codex 版本的支持保证。

## 3. 本适配的支持范围

- Nacos 登录与 Token：保留环境变量来源；macOS 增加页面填写。
- Client/Admin 使用通用的独立/共用认证规则；下游 MCP/Agent 当前仍使用独立环境变量认证。
- Linux 当前仅支持无需认证或环境变量；原生 Windows 因现有 POSIX 文件锁依赖不能启动。
- OAuth 和其他 Nacos 认证插件不在当前 Codex 扩展范围；其他适配按自身能力声明。
- Codex 设置页与 SVG 72–74 的布局、字段和文案映射见 [UI 规格](resource-center-ui-spec.md#45-设置)
  及[图册](ui-storyboard.md)。

以上为当前实现边界，后续变化在本适配维护，不写入通用能力要求。

## 4. 验收状态与追踪

通用验收编号见[初始化、凭据与默认值验收](../../specs/onboarding-acceptance-spec.md)，
Codex 执行结论见[测试矩阵 TM24–TM28](test-matrix.md)。

dev.13 引导与预填已获用户反馈可用。dev.14 核心/协议、禁网浏览器、真实钥匙串验证
分别记录；macOS 页面账号密码保存已获用户确认，钥匙串拒绝/重试与应用跨重启闭环
仍待验。dev.15 增加本机默认目录、标签和可选自定义引导，真实应用目录引导仍待验。
规范提取不改变这些结论，不将 Codex 的结果外推到其他 Agent。
