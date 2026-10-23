# 本地安装细节

本页供 Codex 自动安装和开发者排查使用。普通使用者从 [README](../README.md#安装已发布的-zip)
选择桌面上传或把 ZIP 路径交给 Codex，无需手写清单。

## 给执行安装的 Codex

- 读取用户指定的 ZIP，核对 `plugin.json` 的名称、版本以及 `server/nacos-registry.pyz`；
  先检查压缩包中的路径再解压，保留隐藏文件。确认 Python 3.11+ 和当前 CLI 的插件命令可用。
- 有同名 `.zip.sha256` 时先比对；缺少时可从用户指定的官方 Release 获取对应文件。
  无法取得预期摘要时说明尚未完成完整性比对，不宣称校验通过。
- 先查看已有 marketplace 和插件版本。首次安装可用下面的固定目录；已有安装时沿用已核实的
  来源路径，保留其他插件条目、用户配置和插件私有状态。使用 CLI 支持的安装流程，不直接改缓存。
- 完成后检查安装状态，尝试 `nacos_status` 和资源中心；当前对话未加载工具时说明需要新会话
  或完整重启，并报告待验证项。Nacos 连接与凭据在后续初始化中设置，不随安装包上传或提交。

## 手动安装发布包

从 [GitHub Releases](https://github.com/nacos-group/nacos-plugin/releases) 打开准备安装的版本，
下载 `nacos-ai-registry-<version>.zip` 和 `nacos-ai-registry-<version>.zip.sha256`。
不要选择 `-source.zip` 或 GitHub 自动生成的 Source code；它们不包含已构建的运行程序。
以下示例适用于首次安装；版本号替换为实际下载版本，每一步成功后再继续。

### 1. 检查环境与安装包

在终端检查 Python 和 Codex CLI，再进入两个附件所在的目录：

```sh
python3 --version
codex plugin --help
cd "$HOME/Downloads"
PLUGIN_VERSION='0.1.0-dev.10'
PLUGIN_ZIP="nacos-ai-registry-${PLUGIN_VERSION}.zip"
shasum -a 256 -c "${PLUGIN_ZIP}.sha256"
```

Python 需为 3.11 或更高版本。Linux 若没有 `shasum`，可改用
`sha256sum -c "${PLUGIN_ZIP}.sha256"`。校验应显示对应 ZIP 为 `OK`；失败时重新下载，
不要继续解压或安装。示例版本号不代表该版本已发布，以 Release 附件为准。
如果 `codex` 不在 PATH 或不支持 `plugin` 命令，先安装或更新支持插件的 Codex CLI；
参见[官方 CLI 安装说明](https://developers.openai.com/codex/cli/)及当前 CLI 的帮助。

### 2. 解压到固定目录并生成清单

先查看 `codex plugin marketplace list` 和 `codex plugin list`。如果已有
`local-nacos-registry`，核对并沿用它的目录；保留现有清单中的其他插件条目。
下面使用新的个人固定目录，不应设在源码仓库、下载目录或临时目录中：

```sh
NACOS_MARKETPLACE="$HOME/.local/share/nacos-ai-registry/marketplace"
NACOS_PLUGIN_DIR="$NACOS_MARKETPLACE/plugins/nacos-ai-registry"
mkdir -p "$NACOS_MARKETPLACE/plugins"
mkdir "$NACOS_PLUGIN_DIR" && unzip -q "$PLUGIN_ZIP" -d "$NACOS_PLUGIN_DIR"
```

如果插件目录已存在，`mkdir` 会阻止覆盖，请先核对已有版本并按升级流程处理。
解压后应直接存在 `plugins/nacos-ai-registry/plugin.json`、`.mcp.json`、`.codex-plugin/`
和 `server/nacos-registry.pyz`，不应再多套一层 ZIP 文件名目录。保留全部隐藏文件。

在外层生成 marketplace 清单。以下命令仅在清单不存在时写入；已有清单需合并插件条目：

```sh
mkdir -p "$NACOS_MARKETPLACE/.agents/plugins"
(set -C; cat > "$NACOS_MARKETPLACE/.agents/plugins/marketplace.json" <<'JSON'
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
JSON
)
```

最终目录结构为：

```text
marketplace/
├── .agents/plugins/marketplace.json
└── plugins/nacos-ai-registry/
    ├── plugin.json
    ├── .mcp.json
    ├── .codex-plugin/plugin.json
    ├── server/nacos-registry.pyz
    └── skills/ …
```

### 3. 注册并安装

```sh
codex plugin marketplace add "$NACOS_MARKETPLACE"
codex plugin add nacos-ai-registry@local-nacos-registry
codex plugin list
```

确认列表中的来源、版本和安装状态符合预期。保留固定目录作为后续重装与更新的来源，
不要手动编辑 Codex 管理的插件缓存。已注册的源可以在桌面插件列表中找到后安装。
命令以当前 `codex plugin --help` 和[官方本地插件说明](https://developers.openai.com/plugins/build/plugins)为准。

### 4. 在 Codex 中验证

在对话中选择 Nacos AI Registry，调用 `nacos_status`；首次安装尚未初始化时，返回未配置状态是正常结果。
再打开资源中心，确认页面可显示，然后按[使用说明](installation.md#初始化)初始化连接。插件列表显示已安装只说明安装成功，
不代表本次对话已加载工具，也不代表 Nacos 连接可用。
如果工具尚未出现在当前会话，打开新会话；若仍缺少工具或页面入口，完整退出再重新打开 Codex。
页面入口及排查步骤见[资源中心](resource-center.md)。

## 安装源码构建的产物

源码构建会直接生成完整的 `dist/marketplace/`，可以跳过 ZIP 解压和清单编写步骤。
在 `agent-plugins/codex/`（源码 ZIP 解压后为 `codex/`）执行：

```sh
codex plugin marketplace add "$(pwd)/dist/marketplace"
codex plugin add nacos-ai-registry@local-nacos-registry
```

构建步骤见 [README](../README.md#从源码构建插件包)。原始源码目录缺少已构建的运行程序，不能直接安装。
也可以将完整的 `dist/marketplace/`（包含隐藏的 `.agents/`）复制到固定目录后注册该目录。
