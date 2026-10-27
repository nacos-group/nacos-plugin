<!-- Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 -->

# Nacos AI Registry for Qoder

把 Nacos AI Registry 接入本地 Qoder：在普通任务中发现并复用注册中心里的 Skill、
MCP 工具和远端 Agent，也能把本地技能上传、发布和显式更新。

本适配位于 `agent-plugins/qoder/`，当前版本 `0.1.0`。它独立构建和分发，不进入根 Maven
构建，不复制 JAR 到 Nacos Server，也不依赖 `agent-plugins/codex/` 的任何源码或状态路径。
`0.1.0` 的适配内容与开发预览 `0.1.0-dev.8` 相同，去掉 dev 后缀不放宽任何验收边界：
自动化层已验证，真实宿主安装、系统钥匙串、真实 Nacos 与同会话加载仍待逐项验收。

| 内容 | 入口 |
| --- | --- |
| 产品与完整设计 | 仓库 `agent-plugins/specs/`（通用规范，不随本目录源码包交付） |
| Agent 插件通用开发原则 | 仓库 `agent-plugins/README.md` 的“开发原则” |
| Qoder 适配选择与边界 | [专属规范](specs/README.md) |
| 逐项能力、证据与未通过项 | [兼容记录](specs/compatibility.json) |
| 历史开发预览与逐版本验证 | [开发预览记录](specs/development-preview.md) |

## 能做什么

| 场景 | 插件提供的能力 |
| --- | --- |
| 初次连接 | `nacos-setup` 用原生分步选项收集地址、命名空间、认证协议和下游用途；秘密走本机系统对话框与钥匙串。 |
| 使用团队技能 | 搜索、免安装预览、确切版本安装到技能目录，并显式更新或恢复本地改动。 |
| 共享自己的技能 | 本地盘点、上传预检、草稿、提交与发布，保留来源和归属。 |
| 使用工具和远端 Agent | 发现已注册的 MCP 与 A2A 0.3.0 Agent，免安装试用后再决定保存绑定；注册由原生连接器另行确认。 |
| 为普通任务找帮助 | `nacos-find-capabilities` 在缺少合适能力时按预算搜索注册中心，复用策略为 `ask`（默认）/`auto`/`never`。 |
| 页面操作 | 未实现；当前只有对话工作流与 MCP 工具。 |

## 运行前置

- Python 3.11+，且 Qoder 能在 PATH 找到 `python3`。安装产物内置纯 Python PyYAML，
  使用者不需要 pip、Node.js 或 Java。
- macOS：原生系统对话框录入凭据并保存到钥匙串，这是推荐路径。
- Windows 不支持（本地状态锁使用 `fcntl`）；Linux 只有 CI 覆盖测试与构建，
  宿主安装和凭据入口尚未实测。
- 凭据不经过聊天、工具参数、仓库文件或宿主 MCP 配置；插件状态里只保存不可逆的引用。

## 安装

两种方式都安装同一个包：`nacos-ai-registry-qoder-<version>.zip`（不要用 `-source.zip`）。
包根目录含 `.qoder-plugin/plugin.json`、`.mcp.json`、`skills/`、`assets/`、`server/` 与完整源码。
MCP 以 `python3 ${QODER_PLUGIN_ROOT}/server/nacos-qoder.pyz serve` 在使用者本机启动。

### 方式一：Qoder Desktop 页面导入

1. 打开 **Extensions → Plugins → Add Plugins → Upload Plugin**，选择安装 ZIP。
2. 在插件详情里启用插件。
3. 新建一个本地会话，让宿主重新发现工具 schema。

### 方式二：qodercli

`qodercli plugins install` 接受插件**目录**或远端 HTTPS `.zip` URL，不接受本地 ZIP 文件路径；
本地 ZIP 先解压，或直接用构建产生的展开目录（下文 `dist/nacos-ai-registry`）：

```sh
qodercli plugins validate ./agent-plugins/qoder/dist/nacos-ai-registry --strict --json
qodercli plugins install ./agent-plugins/qoder/dist/nacos-ai-registry
qodercli plugins list
```

`--scope` 可选 `user`（默认，全局）、`project`（提交到版本库）、`local`（个人、不提交）。
开发调试可免安装临时加载，退出即失效，不写插件配置：

```sh
qodercli --plugin-dir ./agent-plugins/qoder/dist/nacos-ai-registry
```

以上基于本机 `qodercli` 1.1.46 的 `--help`，其他版本先核对实际命令；不要照搬 Codex marketplace。
卸载为 `qodercli plugins uninstall nacos-ai-registry`，或在 Desktop 插件页面移除。
升级重新构建并通过宿主安装/更新入口执行，不直接编辑宿主缓存。

### 安装后初始化

在本地会话里先调用 `nacos_status` 确认工具已加载，再运行 `/nacos-ai-registry:nacos-setup`
按原生分步选项完成接入：注册中心地址、命名空间、认证协议（`none`/`login`/`token`）、
凭据来源与下游用途。秘密通过本机系统对话框录入，不要发到对话里。

默认技能目录为 `~/.qoder/skills`，项目作用域使用用户明确选择的 `<workspace>/.qoder/skills`；
插件状态独立保存在 `~/.qoder/state/nacos-ai-registry`，可用 `NACOS_QODER_HOME` 指定，
不读取 Codex 的 `NACOS_PLUGIN_HOME`。卸载插件与清理托管技能、原生 MCP 连接器分别选择，
都不会自动删除 Nacos 上的资源。

## 从源码构建插件包

构建环境需要 macOS 或 Linux、Python 3.11+。首次 checkout 需要安装锁定的 PyYAML 6.0.3；
源码 ZIP 已内置该依赖，重建时不需要 pip，也不需要连接 Nacos。

```sh
cd agent-plugins/qoder
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_package.py
```

用下载的源码 ZIP 时，解压后在其根目录（含 `qoder/` 与 `LICENSE`）执行：

```sh
python3 -I -S -B qoder/scripts/build.py
python3 -I -S -B qoder/scripts/check_package.py
PYTHONPATH=qoder/src:qoder/vendor/pyyaml python3 -S -B -m unittest discover -s qoder/tests -v
```

所有产物生成在 `dist/`，`<version>` 取自 `.qoder-plugin/plugin.json`：

| 产物 | 用途 |
| --- | --- |
| `nacos-ai-registry-qoder-<version>.zip` | 可分发的安装包：manifest、`.mcp.json`、Skills、图标、zipapp 运行程序、许可证及同一份完整源码。 |
| `nacos-ai-registry-qoder-<version>-source.zip` | 可独立重建的源码包，根下为 `qoder/`、`LICENSE` 与 `build-info.json`，内置 PyYAML 源码。 |
| 两个 ZIP 各自的 `.zip.sha256` | 与 ZIP 一同分发；校验用 macOS `shasum -a 256 -c <文件名>.sha256` 或 Linux `sha256sum -c`。 |
| `nacos-ai-registry/` | 安装包的展开目录，可直接用于 `qodercli plugins install` 和检查打包结果。 |

版本号必须在 `.qoder-plugin/plugin.json`、`src/nacos_qoder/__init__.py` 和
`src/nacos_registry/__init__.py` 三处一致，否则构建直接失败。ZIP 使用固定时间戳和
stored 压缩，`build-info.json` 记录源码树摘要、基线提交、工作区是否有未提交改动和依赖版本。

`check_package.py` 校验校验和、固定 ZIP 元数据、manifest 与版本、完整且带许可的源码、
隔离环境中的 zipapp CLI 与 stdio `initialize`/`tools/list`/`status`，并用源码包和安装包内源码
各自离线重建，要求两个 ZIP 与 runtime 字节一致。`dist/` 已被 Git 忽略：维护者只提交源码，
真实测试配置、凭据和操作记录始终留在仓库外，不能先放进这些目录再依赖打包过滤。

仓库 CI `.github/workflows/agent-plugin.yml` 的 `verify-qoder` 作业在 ubuntu-latest 与
macos-latest × Python 3.11/3.13 上执行同样的测试、构建和包检查，并上传 ZIP 与校验和；
它只覆盖自动化层，不代表宿主、钥匙串或 Nacos 验收通过。

## 源码结构

```
qoder/
├── .qoder-plugin/plugin.json   宿主清单：展示元数据、logo、skills 与 mcpServers 入口
├── .mcp.json                   本地 stdio MCP 启动定义，路径使用 ${QODER_PLUGIN_ROOT}
├── src/nacos_qoder/            Qoder 宿主适配层
├── src/nacos_registry/         可移植核心：协议、状态、计划与下游调用
├── skills/                     三个对话工作流
├── specs/                      适配边界与兼容记录
├── assets/nacos-icon.png       清单引用的自带图标
├── scripts/                    构建与包检查
└── tests/                      171 项单元与契约测试
```

分层原则：宿主相关的工具 schema、MCP 帧和本机默认值留在 `nacos_qoder`，业务语义与
一切涉及远端或落盘的判断留在 `nacos_registry`，两者都随安装包和源码包完整交付，
可从源码包的 `qoder/` 独立重建。

### 宿主适配层 `src/nacos_qoder/`

| 模块 | 职责 |
| --- | --- |
| `server.py` | stdio JSON-RPC 循环：`initialize`（含静态发现提示）、`tools/list`、`tools/call` 与错误映射。 |
| `service.py` | 30 个工具的 schema、描述与参数校验，把调用转成核心调用。 |
| `host.py` | 本机默认值：技能目录候选、状态目录、默认标签（系统用户名与 hostname 只是本地标签，不代表服务端身份）。 |
| `__main__.py` | zipapp 入口，提供 `serve` 与排查用的 `status` 子命令。 |

### 可移植核心 `src/nacos_registry/`

| 模块 | 职责 |
| --- | --- |
| `service.py` | 应用核心：配置、诊断、Skill 生产消费、操作计划与恢复；工具与 CLI 共用同一套本地事实。 |
| `schema.py` | 入参与状态结构校验，拒绝越权或自相矛盾的输入。 |
| `store.py` | 带版本的本地状态与串行化操作，`fcntl` 加锁；保存必须带最新修订号，不声明远端事务。 |
| `registry.py` | 固定的 Nacos 3.3 Client/Admin HTTP 契约适配。 |
| `transport.py` | HTTP 传输：显式来源、有界响应，不跟随重定向、不自动重试。 |
| `package.py` | Skill 包校验：大小与路径受限、引用检查，不执行包内任何内容。 |
| `discovery.py` | 意图式发现的本地部分：`ask`/`auto`/`never` 偏好与三个免安装试用。 |
| `downstream.py` | 发现结果的定版快照与独立认证的下游客户端。 |
| `remote.py` | 下游编排：MCP 探测与 A2A 0.3.0 JSONRPC 调用；发现本身从不构成执行授权。 |
| `credentials.py` | macOS 隐藏输入与不同步的钥匙串条目读写。 |
| `credential_service.py` | 凭据工具边界：只接收非敏感意图与上下文，绝不接收明文秘密。 |
| `errors.py` | 定型且不含内容的诊断，不回传原始 HTTP 响应体或秘密。 |

### Skills

| 技能 | 触发与作用 |
| --- | --- |
| `nacos-setup` | 首次接入、改资源入口、凭据异常或排查工具时的原生分步初始化与只读诊断。 |
| `nacos-registry` | 显式管理和使用注册中心资源：搜索、安装、上传、发布、显式更新、调用。 |
| `nacos-find-capabilities` | 普通任务缺能力时的发现入口，正文承载触发条件与原生询问要求，`references/task-completion.md` 承载复用与试用流程。 |

### 30 个工具

- 配置与凭据：`nacos_status`、`nacos_configure`、`nacos_credentials`、`nacos_diagnose`。
- 发现与免安装试用：`nacos_search`、`nacos_configure_discovery`、`nacos_preview_skill`、
  `nacos_mcp_trial`、`nacos_agent_trial`。
- 本地盘点与归属：`nacos_my_skills`、`nacos_scan`、`nacos_onboarding`、`nacos_select`。
- Skill 生产与消费：`nacos_upload_preview`、`nacos_upload_plan`、`nacos_publish_plan`、
  `nacos_install_plan`、`nacos_skill_status`、`nacos_uninstall_plan`、`nacos_verify_skill`。
- 操作执行与恢复：`nacos_apply`、`nacos_inspect_operation`、`nacos_reconcile`、`nacos_recover`。
- MCP 与远端 Agent：`nacos_discover`、`nacos_connection_plan`、`nacos_disconnect_plan`、
  `nacos_mcp_probe`、`nacos_agent_send`、`nacos_agent_task`。

所有写操作都是先出计划、再 `nacos_apply` 落盘的两步；计划带授权上下文，上下文变化或
修订过期会被拒绝，不做静默覆盖。

## 设计约束与验收边界

业务契约来自仓库 `agent-plugins/specs/` 的通用规范（初始化、凭据管理、装配同步、
能力发现、Agent 互通、打包分发与验收场景）。本目录只记录 Qoder 的入口映射和实现选择，
不把宿主细节回写成所有应用的要求；逐条映射见 [专属规范](specs/README.md)。
反复出现且容易被弱化的几条：

- 发现、可达、已保存、宿主已加载、本轮可调用与实际使用是六件分开的事实，各自需要自己的证据。
- `ask` 偏好必须实际调用宿主原生询问工具，不能在对话里列出按钮样式的选项；
  未回答、关闭或超时都不算同意。
- 注册中心凭据不复用于下游服务；下游凭据更换必须重新绑定。
- MCP 绑定不等于原生注册，同会话加载需用户重载 Skills 或经原生连接器管理注册；
  插件没有刷新接口，也不会自动重启应用。
- 默认命名空间（ID `public`）不表示资源公开；`credentialStatus.ready` 只表示凭据可读取，
  不证明 Nacos 接受。

当前仍待完成的验收项（真实新会话的发现触发与询问渲染、同会话加载、真实钥匙串与 Nacos、
带配置和资源的卸载清理）逐项记录在 [兼容记录](specs/compatibility.json)，不继承 Codex 的结论。
