# Nacos AI Registry for Codex

在 Codex 中查找和使用 Nacos AI Registry 里的技能、MCP 工具和远端 Agent，也可以把自己开发的
技能上传、发布给团队使用。插件同时提供对话引导和资源中心页面，连接配置、资源管理都可以从这里开始。

当前源码版本为 **0.1.0**。安装包与 Nacos Server 插件分别构建、分别发布；已发布附件以
[GitHub Releases](https://github.com/nacos-group/nacos-plugin/releases)为准。

## 能做什么

| 场景 | 当前功能 |
| --- | --- |
| 初次连接 | 逐步确认地址、命名空间、认证及技能目录；macOS 可在页面填写凭据并保存到钥匙串，也可选择环境变量。 |
| 使用技能 | 搜索、读取、安装、检查更新、处理冲突、恢复和卸载；可盘点自己选定目录中的已有技能。 |
| 开发和共享技能 | 预览上传内容、保存草稿、提交/发布、查看自己的版本；按 Nacos 实际权限和发布流程执行。 |
| 使用工具和 Agent | 发现已有 MCP 服务和 A2A Agent，核对端点、独立认证和调用结果，按需保存本地连接。 |
| 为普通任务寻找帮助 | 缺少适用能力时尝试发现，先读取技能或试用服务，再按“询问 / 自动保存 / 不保存”决定是否长期复用。模型自行判断是否采用候选。 |
| 页面操作 | 已接入、发现资源、我的资源，以及独立设置、本地技能和待处理操作；支持全局页面与当前对话侧栏。 |

本版面向 **本地执行的 Codex**，运行需要 Python 3.11+。macOS 支持页面凭据输入；Linux 使用
无认证或环境变量；原生 Windows 暂不支持。服务端按 Nacos 3.3.0-RC 的固定 API 基线适配。
其他版本和系统的支持边界见[兼容说明](docs/compatibility.md)。

## 安装已发布的 ZIP

下载 `nacos-ai-registry-0.1.0.zip`（或 Release 中实际提供的版本），不要选 `-source.zip`
或 GitHub 自动生成的 Source code。确保本机已安装 Python 3.11+，Codex 能找到 `python3`。
下面两种方式任选一种。

### 方式一：在桌面插件页面安装

1. 打开 Codex 所在桌面应用的 **插件** 页面，选择 **上传插件包 / Upload plugin archive**。
2. 选择下载的 ZIP，点击 **添加插件 / Add plugin**。
3. 打开插件详情，若显示 **安装 / Install**，点击安装。
4. 回到本地 Codex 对话，通过 `@` 选择 **Nacos AI Registry**，按下文初始化。

这条路径会把插件包上传到账户，再安装到本机；上传与公开上架是不同操作，可见范围以共享设置为准。
若账户没有上传入口，或希望插件包始终留在本机，使用方式二。
界面入口可能因应用版本与权限不同而变化，详见[安装说明](docs/installation.md)与
[官方插件说明](https://learn.chatgpt.com/docs/plugins)。

### 方式二：让 Codex 自动完成本地安装

把下面这段话发给能够操作本机文件的 Codex，只替换 ZIP 的绝对路径：

```text
请把 /absolute/path/nacos-ai-registry-0.1.0.zip 安装到当前 Codex。按包内 codex/docs/local-installation.md 的说明完成本地安装和验证；保留已有插件配置、凭据和本地技能，不上传到账户。
```

使用 Codex CLI 时也可以复制下面的命令，替换路径后执行：

```sh
codex '请把 /absolute/path/nacos-ai-registry-0.1.0.zip 安装到当前 Codex。按包内 codex/docs/local-installation.md 完成本地安装和验证；保留已有插件配置、凭据和本地技能，不上传到账户。'
```

Codex 会核对安装包、解压到固定目录、登记本地来源并完成安装。CLI 需要已登录，并获得执行安装所需的
本机访问权限；这是一条安装协助指令，`codex plugin add` 本身不直接接收 ZIP。
具体命令留在[本地安装细节](docs/local-installation.md)，日常安装不需要手写 marketplace。

## 初始化与开始使用

在本地 Codex 对话中选择插件，发送：

```text
初始化 Nacos AI Registry，先调用 nacos_status 检查本地工具。
```

引导会逐项确认 Nacos 地址、命名空间、用途和认证方式。macOS 选择页面填写时，Codex 可以先把
非敏感信息填入侧栏设置，你再亲自输入用户名、密码或 Token 并保存。凭据不需要发送到聊天中。

不需要自定义技能目录时，新配置默认安装到 `~/.agents/skills`；已存在的该目录及
`$CODEX_HOME/skills` 可作为扫描候选。已有配置会保留，扫描和上传都需要单独选择。
完整默认值和认证说明见[初始化指南](docs/installation.md#初始化)。

完成配置后，可以直接说“打开 Nacos 资源中心”“查找并安装某个技能”或“连接这个 MCP 服务”。
也可以直接描述工作需求，由模型判断是否需要发现能力。在“设置 → 能力发现”中可选择：

- **询问是否安装**（默认）：资源有效帮助完成任务后，询问是否保存供下次使用。
- **有效使用后自动安装**：按已有权限和计划保存本次有用的资源。
- **不安装，也不询问**：仍可发现和试用，任务结束后不主动保存。

上述偏好只影响解决任务时的隐式发现；你主动要求安装时按该请求处理。
MCP 配置已保存、Codex 已加载工具和本次任务已调用分别确认。当前桌面没有开放控制 socket 时，
插件不能保证同一对话即时刷新；可以继续使用授权的试用接口，或在 MCP 设置中重启连接后核对。

安装后若工具或页面没出现，先确认使用的是本地执行环境，再尝试新建本地对话；仍然显示旧入口时
完整退出并重开应用。设置按钮打开云端对话时，回到本地对话初始化即可，无需因此卸载重装。
更多排查见[安装与恢复](docs/installation.md)、[页面入口](docs/resource-center.md)。

## 从源码编译和启动

开发环境需要 Python 3.11+；前端测试需要 Node.js 22+。插件运行和打包不需要 Maven。
从仓库根目录执行以下命令；若使用源码 ZIP，先进入解压目录的 `codex/`，跳过第一行：

```sh
cd agent-plugins/codex
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
PYTHONPATH=src .venv/bin/python -m nacos_registry --version
```

先用仓库外的临时状态目录检查启动，避免开发调试改动日常配置：

```sh
NACOS_DEV_STATE=$(mktemp -d)
PYTHONPATH=src .venv/bin/python -m nacos_registry --state-dir "$NACOS_DEV_STATE" status
```

尚未配置时返回未初始化状态是正常的。需要单独调试 MCP 服务时运行：

```sh
PYTHONPATH=src .venv/bin/python -m nacos_registry --state-dir "$NACOS_DEV_STATE" serve
```

`serve` 通过标准输入/输出处理 MCP 请求，等待客户端连接，不会启动浏览器或弹出独立网页；
终端调试结束可按 Ctrl+C。要在 Codex 中使用页面和完整插件，请继续打包安装。

### 构建可安装包

仍在 `agent-plugins/codex/` 中执行：

```sh
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_package.py
```

依赖安装完成后，这两步可以离线运行，不连接 Nacos。构建会校验版本一致性，并生成兼容 manifest、
内置依赖的运行程序、离线页面、源码及校验和；包检查还会验证文档链接、独立重建与隔离启动。

| `dist/` 中的产物 | 用途 |
| --- | --- |
| `nacos-ai-registry-0.1.0.zip` | 安装包；按上面的任一方式安装。 |
| `nacos-ai-registry-0.1.0-source.zip` | 源码包；保留 `codex/` 与通用 `specs/` 的目录关系。 |
| 两个 ZIP 对应的 `.sha256` | 文件完整性校验，发布时与 ZIP 一起提供。 |
| `marketplace/` | 已生成的本地来源，供开发调试安装使用。 |
| `nacos-ai-registry/` | 安装包的展开目录，供检查产物使用。 |

直接调试构建目录见[源码产物安装](docs/local-installation.md#安装源码构建的产物)。
安装后的插件只需要能找到 `python3`，不需要 pip、Node.js 或源码虚拟环境。

## 开发约定与验证

先遵循上一层的[Agent 插件开发原则](../README.md#开发原则)。Codex 适配还需注意：

- **明确代码分层。** `service.py`、`registry.py`、`remote.py` 等处理资源流程；`hosts/` 处理
  Codex 路径、受管配置和刷新；`skills/` 承载对话引导；`ui/` 分离状态、桥接、组件和主题。
  通用行为变更更新 `../specs/`，具体工具映射和 UI 设计更新本目录 `specs/`。
- **保持包内入口一致。** `plugin.json` 与 `src/nacos_registry/__init__.py` 的版本同步修改。
  `mcp.json` 和 `.mcp.json` 保持一致的启动行为；兼容 manifest、zipapp 和页面由构建生成。
  改源码后重新构建，通过原安装来源升级，不直接编辑 Codex 缓存。
- **保护用户环境。** MCP 只修改自己拥有的配置块，保留用户的其他设置和工具限制。凭据经安全通道保存；
  不在工作流、工具参数、日志或样例中加入明文秘密。开发联调状态和服务都放在仓库外。
- **按层核验结果。** 页面调用、模型可见工具、原生加载和实际业务使用分别验证；界面跟随 Codex 主题。
  修改流程时同时检查[通用交互](../specs/resource-center-interaction-spec.md)、
  [Codex UI 适配](specs/resource-center-ui-spec.md)和[测试矩阵](specs/test-matrix.md)。

提交前按改动范围运行相应测试；版本或打包改动应执行完整检查：

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
node --test tests/test_ui_model.cjs
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_package.py
```

详细模块职责与验证方法见[开发指南](docs/development.md)。打包前保证私有环境文件不在源码目录中；
`dist/` 已忽略，不提交生成包。真实应用中仍待验证的内容保留在[TODO](specs/TODO.md)，不以单元测试代替。

## 发布与更多文档

`0.1.0` 使用组件 tag `nacos-ai-registry-v0.1.0`。维护者从确定的干净提交构建，在 GitHub Release
提供安装包、源码包、校验和与发行说明，具体操作见[发布指南](docs/releasing.md)。
源码版本更新不会自动发布，GitHub Release 与 Codex 公开插件目录上架也是分别进行的流程。

- [通用规范](../specs/README.md)与[Codex 专属规范](specs/README.md)
- [兼容范围](docs/compatibility.md)与[测试矩阵](specs/test-matrix.md)
- [初始化、升级和卸载](docs/installation.md)
- [源码来源与迁移记录](docs/migration.md)
