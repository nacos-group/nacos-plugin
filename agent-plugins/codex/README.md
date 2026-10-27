# Nacos AI Registry for Codex

将 Nacos AI Registry 接入 Codex。本组件位于 `agent-plugins/codex/`，独立于
仓库中的 Nacos Server Java 插件，不需要复制 JAR 到 Nacos，也不由根 Maven 构建。

当前提供 `0.1.0-dev.21` 首版验收候选的源码与可安装包；P0/P1 的实现覆盖和剩余发布门槛见 TODO。
完整设计目标不等于本版已交付能力。
首期包含 Skill 生产/消费、显式双向更新和初始化盘点，以及已有 MCP/远端 Agent 的发现
与调用。[简洁工作台](specs/resource-center-ui-spec.md)已按选定图册重构为三主视图、
类型专属详情和独立设置；本地自动测试与浏览器交互已验证，基础功能经使用者自测可用，
现进入首版验收。完整内嵌闭环与首次连接三步向导等差距继续在 TODO 中单列。
分层结论见[测试矩阵](specs/test-matrix.md)。
创建后提醒和 Hooks 不纳入首期。

| 内容 | 入口 |
| --- | --- |
| 产品与完整设计 | [通用规范](../specs/README.md) |
| Codex 适配设计 | [专属规范](specs/README.md) |
| 当前范围、待办和决策 | [TODO](specs/TODO.md) |
| 来源、仓库与迁移检查 | [迁移记录](docs/migration.md) |
| 源码、安装包与兼容要求 | [打包分发](specs/distribution-spec.md) |

版本独立采用 SemVer，tag 为 `nacos-ai-registry-v<version>`。不沿用 Server 插件的版本
映射。运行依赖与支持边界见兼容说明，私有测试环境信息不进入仓库；未经验证的 Agent 应用与服务器组合不声明支持。
仓库只保存插件源码、内置工作流和隔离样例，用户业务资源和凭据留在用户环境。

dev.15 的初始化会区分认证方式和凭据提供方式。macOS 用户可让本地对话预填侧栏设置，
再亲自在页面填写用户名、密码或 Token，保存到本机钥匙串；无需手动设置环境变量，
日常更换凭据也不要求重启。环境变量仍是可选方式；Linux 尚未实现页面凭据存储，原生 Windows 当前不支持启动。
macOS 账号密码页面保存已获用户实测确认，其他验收边界见[初始化规范](specs/credential-onboarding-spec.md)。

初始化还会询问是否自定义技能目录。不需要时，新配置使用个人 `~/.agents/skills` 安装目录，
已存在的个人目录和 `$CODEX_HOME/skills` 作为扫描候选；具体路径会在保存前展示。已有配置保持
不变，也可在“设置 → 技能目录”添加默认目录。保存目录不等于扫描或上传。

`nacos-find-capabilities` 在任务需要专业识别/检索、业务数据、团队规则或
专用工作流且没有已知适用能力时，就尝试在已配置的 Nacos 中搜索 Skill、MCP 和 Agent，
不要求先失败或在问题中提到 Nacos。首次检索没有有效结果时也可回退到发现。
规划、回退与交接共用一轮最多 3 次的预算；Skill 描述、搜索工具和 MCP 初始化说明使用同一标准。
已有能力能给出有效结果时优先直接完成任务；只读搜索不会自动授权安装或远端执行。
这依赖新会话加载并选择发现入口，实际隐式触发效果仍待验证，详见
[发现适配与测试场景](specs/capability-discovery-spec.md)。

可在“设置 → 能力发现”选择：询问是否安装（默认）、有效使用后自动安装、不安装也不询问。
它只影响解决问题时发现的能力，主动要求安装不受影响。先通过校验后的 Skill 内容或不保存连接的
MCP/Agent 接口尝试解决任务，再按策略保存本次真正有用的资源；询问优先采用交互式选项。
MCP 保存后可尝试原生刷新：需要当前 Codex App Server 提供控制 socket；stdio-only 桌面当前无法
由插件触发该刷新，可使用不安装的 MCP 调用，或在应用 MCP 设置中 Restart 后核对当前会话。
模型仍自行选择合适能力，试用、保存、原生加载和实际调用分别确认。

## 安装已发布的 ZIP

准备 Python 3.11+（macOS 或 Linux），从 [GitHub Releases](https://github.com/nacos-group/nacos-plugin/releases)
下载 `nacos-ai-registry-<version>.zip`，不要选 `-source.zip` 或 Source code。

### 方式一：在桌面插件页面选择 ZIP

如果当前账户的插件页面提供 **上传插件包 / Upload plugin archive**：

1. 打开桌面应用的 **插件** 页面，在创建或更多菜单中选择 **上传插件包**。
2. 选择下载的 ZIP，点击 **添加插件 / Add plugin**。
3. 打开生成的插件详情，若显示 **安装 / Install**，点击安装。
4. 在 **本地 Codex 对话** 中通过 `@` 选择 Nacos AI Registry，发送“初始化 Nacos AI Registry，先调用 nacos_status 检查本地工具”。

这条路径无需解压或编写 marketplace。它会将插件包上传到账户，入口和可接收的组件取决于账户权限。
上传与共享、公开上架是独立操作；可见范围以插件的共享设置为准。
插件包含本地 MCP 程序，需要在使用者电脑上运行。
若安装后的“设置”按钮打开了云端对话，出现“Skill 已读取、工具未加载”，请切回 Codex，
选择本地项目与“本地 / Local”执行环境，再按第 4 步初始化。仅出现这个提示无需卸载重装。
若没有上传入口或上传被拒绝，使用下面的本地安装方式。
更多说明见[安装与验证](docs/installation.md)。

### 方式二：让 Codex 自动安装

把下面一句话发给能够操作本机文件的 Codex，只需替换 ZIP 的绝对路径：

```text
请把 /absolute/path/nacos-ai-registry.zip 安装到当前 Codex。按包内 codex/docs/local-installation.md 的说明完成本地安装和验证，保留已有插件配置及私有数据。
```

在终端使用 Codex CLI 时，同样只需一条命令：

```sh
codex '请把 /absolute/path/nacos-ai-registry.zip 安装到当前 Codex。按包内 codex/docs/local-installation.md 的说明完成本地安装和验证，保留已有插件配置及私有数据。'
```

这会开启由 Codex 执行安装的对话，需要已登录的 CLI，并按界面提示授予所需访问权限。
当前原生 `codex plugin add` 不直接接受 ZIP 路径；解压和本地源登记由 Codex 完成，
安装包留在本机。完整命令仅供排查或手动操作，见[本地安装细节](docs/local-installation.md)。

## 从源码构建插件包

构建环境需要 macOS 或 Linux、Python 3.11+；运行测试还需要 Node.js 22+。
安装后的插件只需要 Codex 能找到 `python3`，不需要 Node.js、pip 或 Maven。
PyYAML 会随运行包内置；Windows 暂不声明支持。

从仓库根目录执行：

```sh
cd agent-plugins/codex
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
node --test tests/test_ui_model.cjs
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_package.py
```

使用下载的源码 ZIP 时，解压后进入其中的 `codex/`，从创建虚拟环境这一步开始。
依赖安装完成后，构建与包检查均可离线执行，也不需要连接 Nacos。
包检查会验证 manifest、图标资源、校验和、文档链接、源码独立重建，以及隔离环境中的 CLI、MCP 和页面资源。

所有产物生成在 `dist/`，其中 `<version>` 来自 `plugin.json`：

| 产物 | 用途 |
| --- | --- |
| `nacos-ai-registry-<version>.zip` | 可分发的安装包，包含 manifest、Skills、运行程序、许可证及对应源码。 |
| `nacos-ai-registry-<version>-source.zip` | 可独立重建的源码包，保留 `codex/` 与通用 `specs/` 的目录关系。 |
| 上述两个 ZIP 各自的 `.sha256` 文件 | 下载后校验文件完整性，与对应 ZIP 一起分发。 |
| `marketplace/` | 已生成本地 marketplace 清单和完整插件，可直接用于下面的本地安装。 |
| `nacos-ai-registry/` | 安装包的展开内容，用于检查打包结果。 |

`dist/` 已被 Git 忽略。构建会收集源码、工作流、图标、文档、规范、测试和样例；真实测试配置、
凭据与操作记录应始终保存在仓库外，不能先放进这些目录再依赖打包过滤。

构建后的 ZIP 同样使用上面的两种安装方式。开发者直接使用构建目录调试时，
参见[构建产物调试安装](docs/local-installation.md#安装源码构建的产物)。

## 发布供他人使用的版本

这里的发布是将版本包分发到本仓库的 GitHub Releases；Codex 官方插件目录上架是单独流程，
发布 ZIP 不会自动完成目录上架。当前 `0.1.0-dev.21` 应以预发布版本分发，正式稳定版仍需完成
[TODO](specs/TODO.md) 和[兼容说明](docs/compatibility.md)中的发布门槛。

维护者按以下顺序发布：

1. 同步修改 `plugin.json` 的 `version` 与 `src/nacos_registry/__init__.py` 的 `__version__`，
   更新 README 的版本与验收范围；两处版本不一致时构建会失败。
2. 将改动提交、合并，检出准备发布的提交。确认 `git status --porcelain` 没有输出，
   再完整执行上面的测试、构建和包检查。不要使用此前留在 `dist/` 中的旧包。
3. 检查 `dist/nacos-ai-registry/build-info.json`：版本应正确，`gitBase` 应为准备发布的提交，
   `dirty` 应为 `false`。源码包与安装包必须来自这一次构建。
4. 在仓库外准备发行说明，写明变化、支持环境、安装入口和未完成的验收项，然后创建组件 tag
   和 Release 草稿。下面命令仍在 `agent-plugins/codex/` 中执行，需要 GitHub 推送及发布权限、
   已登录的 `gh`；将发行说明路径替换为实际文件路径。

```sh
PLUGIN_VERSION=$(.venv/bin/python -c 'import json; print(json.load(open("plugin.json"))["version"])')
PLUGIN_TAG="nacos-ai-registry-v${PLUGIN_VERSION}"

git tag -a "$PLUGIN_TAG" -m "Nacos AI Registry ${PLUGIN_VERSION}"
git push origin "refs/tags/${PLUGIN_TAG}"

gh release create "$PLUGIN_TAG" \
  "dist/nacos-ai-registry-${PLUGIN_VERSION}.zip" \
  "dist/nacos-ai-registry-${PLUGIN_VERSION}.zip.sha256" \
  "dist/nacos-ai-registry-${PLUGIN_VERSION}-source.zip" \
  "dist/nacos-ai-registry-${PLUGIN_VERSION}-source.zip.sha256" \
  --repo nacos-group/nacos-plugin \
  --verify-tag --draft --prerelease --latest=false \
  --title "Nacos AI Registry ${PLUGIN_VERSION}" \
  --notes-file /absolute/path/to/release-notes.md
```

每一步成功后再继续；若 tag 已存在，应先核对它指向的提交，不覆盖已发布版本。
在 GitHub 中核对草稿的 tag、四个附件和发行说明后再发布。`dev`、`rc` 等候选版本保留
Pre-release 标记；稳定版满足发布门槛后再移除该标记，并明确选择是否设为最新版本。
下载者应同时获得安装 ZIP 与对应 SHA-256；例如在下载目录使用 macOS 的
`shasum -a 256 -c <安装包文件名>.sha256`，或 Linux 的 `sha256sum -c <安装包文件名>.sha256`。

现有 `.github/workflows/agent-plugin.yml` 会在相关 PR 或手动触发时执行测试和打包，
并保存 ZIP 与校验和为 Actions artifacts。它不会因推送 tag 自动创建或发布 Release；
上述发布步骤需由维护者执行。

## 更多说明

- [本地安装、初始化和恢复](docs/installation.md)
- [开发、测试与打包](docs/development.md)
- [资源中心页面与入口排查](docs/resource-center.md)
- [兼容范围与发布门槛](docs/compatibility.md)

源码入口为 `src/nacos_registry/`，工作流在 `skills/`，manifest 为根目录的 `plugin.json`。
构建生成独立 zipapp、安装 ZIP 和源码 ZIP。提供对话向导、MCP 工具及资源中心页面；各项验收状态见 TODO。
