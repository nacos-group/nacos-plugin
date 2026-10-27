# Codex 能力发现适配

通用触发、搜索预算、资源选择、安装策略、交互询问与当前会话优先使用原则，由
[能力发现规范 §2–3.5](../../specs/capability-discovery-spec.md)定义；本页记录 Codex 的具体映射。

## 1. 入口与设置（dev.20）

- 插件交付 [nacos-find-capabilities](../skills/nacos-find-capabilities/SKILL.md)。description
  覆盖专业识别、业务数据、团队规则和专用工作流等任务信号；保留隐式选择，不要求提到 Nacos。
- `nacos_search` 描述与 MCP `initialize.instructions` 使用相同触发标准、上下文和搜索预算。
  指引为静态内容，不携带本地配置或凭据，不在初始化时发起搜索。
- 不写个人/项目 AGENTS.md，不安装全局 Hook，不监听全部对话。由模型判断是否需要发现，
  每个能力缺口共享最多 3 次、每次 20 条的预算；协议检查不等于模型行为验收。
- `nacos_status.discovery.installPolicy` 返回 `ask | auto | never`，旧状态缺省 `ask`。
  `nacos_configure_discovery` 只保存用户选择。偏好位于插件本地状态，作用于这份本机插件状态，
  与 registry profile 分开，因此不改变连接 fingerprint，不使已有凭据、安装、连接或任务失去归属。
- 设置页新增“能力发现”分组，中英文标签分别对应“询问是否安装（默认）”“有效使用后自动安装”
  “不安装，也不主动询问”。保存只更新偏好，不扫描、调用或安装资源。

## 2. 本次使用与长期复用

| 通用动作 | 工具与行为 |
| --- | --- |
| 状态/发现 | `nacos_status` → `nacos_search`，后续携带返回的 `_context`。上下文改变拒绝旧操作。 |
| Skill 不安装使用 | `nacos_preview_skill` 通过 Client API 下载、校验确切包并返回一个 UTF-8 文件及文件目录；默认 SKILL.md，单文件上限 256 KiB，引用文件用返回的确切版本读取。 |
| MCP 不安装使用 | `nacos_mcp_trial` 不传 tool 时枚举，传当前目录中的工具名与授权参数时调用。每次核对 Nacos 可见性、端点、独立认证与工具目录；最多 5 页/500 工具，不接收任意 URL。 |
| Agent 不保存绑定使用 | `nacos_agent_trial` 读取声明的 A2A 0.3.0 JSONRPC 服务，按任务授权发送；不加入 connections。异步任务保留必要的句柄和原端点快照，由 `nacos_agent_task` 查询/取消。 |
| 持久 Skill | `nacos_install_plan` → `nacos_apply` → `nacos_verify_skill`；原目录、归属、版本、冲突保护不变。 |
| 持久 MCP/Agent | `nacos_connection_plan` → `nacos_apply`；保存 native MCP 受管 TOML 块或 Agent 绑定，凭据独立，原有策略保留。 |

试用边界、未知结果处理和记录最小化统一见[通用 §3.5](../../specs/capability-discovery-spec.md#35-无安装试用的调用契约)。
Codex 将通用事实维度映射为 `route`、`saved`、`hostLoaded`、`currentTurnTools` 和 `realUse`。
MCP 试用返回 `route=registry_mcp_adapter`、`saved=false`、`hostLoaded=not_claimed`；
Agent 试用使用 `route=registry_a2a_adapter`。MCP 执行的是 tools/call，不计为 Codex 原生工具注入。
本地限制读取相同 URL 的 native server 的 `enabled`、`enabled_tools/disabled_tools`；
没有已保存原生配置时仍保留插件操作范围及任务授权检查。

三个消费 Skill 共用 [task-completion](../skills/nacos-find-capabilities/references/task-completion.md)：
执行通用 §3.2–3.3。Codex 的 `ask` 映射到当前可用的 `request_user_input_async`；
其他模式只使用该模式允许的选择工具，不可用时才用会话文字。

隐式发现生成的持久计划传 `discoveryReuse=automatic` 或 `confirmed`，计划与 apply 都检查当前偏好。
`automatic` 只允许 auto，`confirmed` 表示已经获得用户选择且策略不能为 never。
显式管理省略标记；不得为绕过拒绝而省略。状态服务不推断模型意图，也无法独立证明用户确认和业务价值，
由工作流判断并遵守授权；这是执行前的策略保护，不是替代模型行为验收的完整授权系统。

### 2.1 原生 MCP 服务名称（dev.21）

原生配置键使用 `nacos_<资源名>_<12 位身份摘要>`，例如 `nacos_team-tools_0123456789ab`。
资源名转小写，保留 ASCII 字母、数字、连字符、下划线，其他连续字符替换为连字符，
去除首尾分隔符并限制为 32 字符；没有可保留字符时使用 `mcp`。完整名称最多 51 字符，
仅使用 TOML 裸键及原生工具名称可安全使用的字符；资源中心仍显示完整原始资源名。
完整资源身份摘要和冲突保护遵循[通用连接命名与迁移](../../specs/assembly-sync-spec.md#61-原生连接名称与安全迁移)。

已有 `nacos_<20 位摘要>` 配置和旧计划继续兼容。用户明确重新保存时，`hosts/codex.py`
对 TOML 受管块执行通用迁移契约：计划携带旧/新名称与摘要，以单文件原子替换实现，恢复记录保留旧块。
应用加载按第 3 节单独验证。

## 3. Codex 原生 MCP 刷新

依据 [App Server 协议](https://learn.chatgpt.com/docs/app-server)，`config/mcpServer/reload`
读取配置并向已加载线程排队刷新；`mcpServerStatus/list` 可指定 threadId/serverName 查询该线程连接。
当前实现位于 `hosts/native.py`，由 `nacos_mcp_refresh(connectionId, threadId)` 调用：

1. 先核对连接归属、远端可见性和未修改的受管配置，目标必须是当前 `CODEX_HOME/config.toml`。
2. 使用已运行的 App Server Unix WebSocket 控制 socket。默认位置在 CODEX_HOME 下；应用集成
   显式提供 `NACOS_PLUGIN_CODEX_CONTROL_SOCKET` 时可使用该路径。locator 和最终 socket 须属于当前用户；
   兼容 Codex 为 Unix 路径长度限制生成的用户所有符号链接。不会自行启动另一个 App Server。
3. 标准 WebSocket Upgrade → `initialize` → `initialized`，有界读取 `thread/loaded/list`，
   确认传入的**当前会话 ID**在此进程中加载。不从远端资源或其他对话猜测 ID，不恢复/新建线程。
4. 调用 `config/mcpServer/reload`；这是应用级配置刷新，会排队刷新已加载线程，不是单服务专属重启。
   随后只查询选中线程/服务的状态。只有 `runtimeStatus=connected` 且目录成功才报告运行时 available。
5. `currentTurnTools` 与 `realUse` 仍保持未验证；模型须从当前工具目录获取并实际调用原生工具。
   排队受理、运行时工具可用和当前轮次模型可见不是同一事实。

客户端使用标准库实现本地 WebSocket，限制消息大小与等待时间，处理 ping/分片；不批准任何服务端
反向请求，不发送 turn，不修改审批策略。缺少 socket、不同进程中的线程、配置不匹配或超时明确降级，
不安装第二份配置、不杀进程、不改应用启动参数。Windows 等缺少此本地传输时返回不可用。

**验证边界**：隔离 App Server 已验证在同一已加载测试线程中，从无 MCP → 写入配置 → 原生 reload →
枚举 → `mcpServer/tool/call` 成功，不依赖创建替代线程。这个结果证明协议路线可行，不能外推为任意
桌面实例或正在生成的当前轮次已更新。stdio-only 桌面没有提供控制 socket 时插件无法使用该入口；
先通过已有适配完成当前任务，或引导 Settings → MCP servers → Restart 后重新检查当前对话。
新建会话只作最后兼容步骤，不能自动执行。桌面指引依据 [MCP 文档](https://learn.chatgpt.com/docs/extend/mcp)。

### 3.1 原桌面对话即时生效：TODO DISC08

目前缺少让插件访问当前 stdio-only 桌面 App Server 的正式刷新入口，暂不继续用额外 App Server、
应用内部 IPC、修改启动参数或自动重启来模拟成功。保存后新会话的原生调用可用，也不能关闭此项 TODO。

后续在应用开放正式接口或现有控制 socket 后再实施：

- 绑定用户当前桌面进程及当前会话，明确刷新范围与接口权限；复用已有连接，避免重复配置。
- 保存获授权的连接后发起刷新，观察同一会话工具目录是否更新；区分当前生成轮次和下一轮才生效。
- 在同一会话实际原生调用新工具，覆盖成功、超时、断线、用户禁用、重命名及解除接入；不自动同意应用审批。
- 只有完整证据才报告原生可用；无入口或失败时继续适用的 MCP 转调，并说明原生加载尚未完成。

安装仍服从通用策略；此 TODO 不阻塞当前会话通过适配调用完成任务，也不承诺每个 Codex 版本都能热加载。

## 4. 验收与交付

当前源码版本 `0.1.0`，包与源码包包含工作流、设置、试用、原生刷新适配和可读 MCP 名称。
通用 CD-01–34 与本地 [TM29–TM38](test-matrix.md)交叉验证。自动化覆盖策略缺省/持久化、显式例外、
旧自动计划阻断、资源读取/端点隔离、无持久安装试用、错误/未知结果、原生线程验证及加载状态区分。
UI 检查覆盖中英文偏好、保存/重开、连接和资源归属不变；原生实际调用与桌面当前轮次分别记证据。

Skill 入口机制见 [Build skills](https://learn.chatgpt.com/docs/build-skills)；隐式触发、模型是否使用选择工具、
跨模型和跨应用的执行效果仍需真实会话验证。不得将单元测试或一次个例记作整个 CD 矩阵通过。
真实配置、演示服务、私有脚本、模型/线程信息和操作轨迹只留在仓库外，不写入源码或发布包。
