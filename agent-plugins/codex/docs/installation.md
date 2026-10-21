# 本地安装与使用

这是开发预览包。先准备 Python 3.11+，并检查 `python3 --version` 能从宿主的环境执行。
从与源码对应的 ZIP 安装，校验随包提供的 SHA-256。发布包不包含 Nacos 地址、身份或用户资源。

## 安装到 Codex

源码构建会生成 `dist/marketplace/`，内有一个完整插件和 `.agents/plugins/marketplace.json`。
使用目标 Codex 支持的本地 marketplace 流程：

```sh
codex plugin marketplace add /absolute/path/to/marketplace
codex plugin add nacos-ai-registry@local-nacos-registry
```

也可以在桌面插件目录选择对应本地 marketplace 并安装。若当前 CLI 不支持某个命令，以
`codex plugin --help` 和 [官方本地插件说明](https://developers.openai.com/plugins/build/plugins)
为准。安装后确认 `nacos_status` 可调用；需要时打开新会话或重启。账户目录记录、包解析和
本地 MCP 启动是不同结果。不要直接编辑宿主插件缓存。

只有安装包时，将 ZIP 解压为 marketplace 根下的 `plugins/nacos-ai-registry/`，创建：

```json
{
  "name": "local-nacos-registry",
  "interface": {"displayName": "Local Nacos Registry"},
  "plugins": [{
    "name": "nacos-ai-registry",
    "source": {"source": "local", "path": "./plugins/nacos-ai-registry"},
    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
    "category": "Productivity"
  }]
}
```

将该文件保存为 marketplace 根下的 `.agents/plugins/marketplace.json`。不要把外层
marketplace 打进单插件 ZIP。源码只用于开发；先在 `agent-plugins/codex/` 构建，再安装产物。

安装或更新后完整退出并重新打开桌面应用，让插件工具和页面入口重新加载。页面打开方式、
三个主视图、独立设置与新版内嵌验收见[资源中心](resource-center.md)。

## 初始化

运行 **nacos-registry-setup**，或直接说“初始化 Nacos AI Registry”。某些宿主不会展示
manifest 的 setup 入口，此时显式调用已列出的初始化 Skill。初始化不会在安装时自动扫描。

向导需要 Client/Admin 完整 base URL、namespace、身份引用和操作范围。认证支持原生
login、token 引用和明确选定的无认证模式。秘密在进程环境中输入，配置只保存环境变量名；
启动 Codex 的进程需具有这些变量；本地 MCP 还需要显式透传。包通过 OpenAI 扩展引用
`.mcp.json`，仅放行以下变量名，不包含值，也不继承全部环境：

| 用途 | 变量名 |
| --- | --- |
| 私有状态目录 | `NACOS_PLUGIN_HOME` |
| Client 登录或 token | `NACOS_PLUGIN_CLIENT_USERNAME`、`NACOS_PLUGIN_CLIENT_PASSWORD`、`NACOS_PLUGIN_CLIENT_TOKEN` |
| Admin 登录或 token | `NACOS_PLUGIN_ADMIN_USERNAME`、`NACOS_PLUGIN_ADMIN_PASSWORD`、`NACOS_PLUGIN_ADMIN_TOKEN` |
| 下游独立 bearer | `NACOS_PLUGIN_MCP_TOKEN`、`NACOS_PLUGIN_AGENT_TOKEN` |

profile 的 `usernameEnv`、`passwordEnv`、`tokenEnv` 使用对应变量名。未选中的认证方式
无需设置变量。需要额外的下游身份时，在自己维护的插件源码 `.mcp.json` 的 `env_vars`
中增加变量名，重建并重新加载；不要将值写入该文件或编辑安装缓存。portable `mcp.json`
保留通用启动声明，Codex 的变量透传以专用声明为准。
修改凭据或身份后重新加载连接并诊断，不在聊天中粘贴密码/token。
普通消费身份只需 Client 读取权限及目标资源的可见性授权，不要求 Admin 权限。
登录或空搜索成功不证明私有资源授权有效；服务端未开启鉴权时也不能证明撤权有效。

明确选择盘点目录和安装目录，例如项目的 `.agents/skills/` 或宿主支持的个人 Skill 根目录。
配置需要绝对路径；插件把系统临时目录别名规范化，拒绝用户资源中的符号链接。
可以跳过盘点，再从初始化入口重新进入。扫描仅列元数据；上传预检会传输 ZIP，因此必须
先选中资源与目标。忽略、仅跟踪、本次上传草稿、提交/发布是不同动作。

## 日常使用

- 说“查找并安装某个 Skill”：搜索、核验确切版本、查看计划、应用，再验证宿主发现与使用。
- 说“上传这个 Skill 的修改”：对选中的候选创建上传计划，处理版本与草稿冲突，再应用。
- 说“发布这个版本”：查看实际可见性、审核状态与计划。submit 可能直接上线；草稿不自动 submit。
- 说“更新或卸载已安装 Skill”：仅处理本插件拥有的内容，本地修改会阻止覆盖。
- 说“连接某个 MCP / 调用某个远端 Agent”：解析权威端点，绑定独立凭据，审阅连接计划。
  MCP 由 Codex 原生连接；A2A 支持非流式 0.3.0 JSON-RPC 调用、查询和取消。

## 状态、恢复与卸载

默认私有状态在 `~/.local/state/nacos-ai-registry/`，可在启动前用 `NACOS_PLUGIN_HOME`
指定其他目录。该目录含用户映射、快照和操作记录，不应提交或共享；凭据值不保存其中。
CLI 与 MCP 使用同一核心和状态，可通过以下方式做无副作用检查：

```sh
python3 server/nacos-registry.pyz --state-dir /absolute/private/state status
```

CLI 的动作参数从 `--input /absolute/path/arguments.json` 或 `--input -` 读取，格式与同名
MCP 工具一致。不要在参数文件中放秘密值。传输或进程失败后，先按 operation ID 检查状态，
不要盲目重试。Skill 本地恢复只恢复已知快照，且会重新核验远端读取权限；不回滚远端发布。

升级后保留状态目录。卸载插件使用宿主支持的 remove/uninstall 流程；这不会删除远端资源。
本地托管 Skill 与 MCP 连接应先按归属单独解除，不要删除整个个人 Skill 或 Codex 配置目录。
