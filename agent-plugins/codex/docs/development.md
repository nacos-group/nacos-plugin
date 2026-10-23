# 开发、构建与验证

需要 Python 3.11+（macOS 或 Linux）。运行包内置 PyYAML 6.0.3 的纯 Python 实现；用户
无需 pip、Maven 或 Node。Python 解释器本身不内置，安装者须预先安装并让应用进程能找到
`python3`。原生 Windows 因 `fcntl` 文件锁依赖无法启动，目录 fsync、权限和凭据服务也需要
适配；不声明支持。Linux 可使用环境变量或无认证，页面直接填写尚未实现。

在 `agent-plugins/codex/` 执行；使用源码 ZIP 时先进入解压目录的 `codex/`：

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-build.txt
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
node --test tests/test_ui_model.cjs
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_package.py
```

开发时额外需要 Node 22+ 运行无第三方依赖的状态/桥接测试；插件运行和打包不需要 Node。

产物在 `dist/`：单插件 ZIP、源码 ZIP、SHA-256，以及供本地测试使用的 marketplace。
安装 ZIP 根目录含 manifest、工作流、图标和独立 zipapp，另含许可证及对应的源码和规范。
源码 ZIP 保留 `codex/` 与 `specs/` 的相对层级，解压后可以独立重建。构建不联网；依赖准备是单独步骤。
构建记录包含组件版本、源码摘要及对应 Git 起点/dirty 状态；开发产物不能冒充正式发行。

代码职责：

| 目录/模块 | 职责 |
| --- | --- |
| `src/nacos_registry/service.py` | 共享计划、操作、Skill 生产消费与盘点。 |
| `credentials.py` / `credential_service.py` / `credential_channel.py` / `credential_crypto.py` | macOS Keychain、凭据事务、一次性 JWE 加密提交；工具参数只收密文。 |
| `registry.py` / `transport.py` | 固定版本的 Nacos HTTP、认证、错误与传输。 |
| `package.py` / `store.py` | 有界包检查、文件摘要、版本化本地状态及恢复。 |
| `remote.py` / `downstream.py` | 原生 MCP 配置和独立认证、A2A 调用与任务绑定。 |
| `src/nacos_registry/hosts/` | Codex 配置的最小修改与归属检查。 |
| `plugin.json` / `mcp.json` / `.mcp.json` / `skills/` | portable 启动声明、Codex 环境变量名透传和工作流；两个入口的命令保持一致。 |
| `assets/` | 插件列表与输入框图标及来源说明；安装包和源码包均保留，manifest 使用包内相对路径。 |
| `specs/` | Codex 专属设计、实施与验收状态。 |
| `../specs/` | 所有 Agent 应用共用的资源契约与功能设计。 |
| `src/nacos_registry/ui/model.js` | 无 DOM/主题依赖的导航、上下文隔离、动作规则与请求时序。 |
| `ui/bridge.js` | MCP App 初始化、工具调用、响应与主题信号的边界。 |
| `ui/components.js` | 安全文本、表单、原行菜单、键盘焦点和单次确认。 |
| `ui/settings-model.js` / `ui/settings.js` | 设置字段语义、地址/认证映射、中英文文案、分区布局、草稿与连接检查状态。 |
| `ui/app.js` / `ui/theme.css` | 资源流程编排及独立 Codex 布局/主题适配。 |
| `ui.py` | 复用本地模块生成全局和对话两个离线 HTML 资源，保留入口身份；无 CDN 或运行时构建。 |
| `tests/` | 不依赖任何真实测试中心的契约与错误路径测试。 |

独立 GitHub Actions 执行本组件的测试、打包及干净运行检查，不调用 Maven，不自动发布。
现有服务端 Java CI 不变。组件 tag 为 `nacos-ai-registry-v<version>`；源码和安装包必须来自
同一组件源码摘要。正式发布前仍须完成 [验收边界](compatibility.md) 与 TODO 的剩余项。

列表展示信息维护在 `plugin.json` 的 `extensions.com.openai.interface`，包括描述、开发者、
网站、支持入口和图标。构建同步到兼容 manifest；仅在 README 写网站不会填充插件详情。
修改这些字段后需重新构建并通过原安装来源更新版本，已安装的旧包不会自动改变。
图标复用 Nacos 项目资源，来源见 [assets/README.md](../assets/README.md)。

真实环境地址、身份、凭据、操作脚本与运行轨迹不得进入仓库、CI 配置、源码 ZIP 或安装包。
需要联调时在仓库外维护私有配置和执行记录；通用测试只能使用合成的样例与协议响应。

页面验证按[测试矩阵](../specs/test-matrix.md)区分核心、协议、浏览器与真实应用。
浏览器验收使用仓库外合成夹具，生产页面不含模拟按钮或测试服务端口。

页面填写由浏览器 WebCrypto 加密，本机通过 macOS Security.framework / CommonCrypto
解密并保存到钥匙串，纯标准库调用，无额外 Python 依赖。协议固定使用 JWE Compact
RSA-OAEP-256 / A256CBC-HS512；临时 RSA 私钥不导出、不持久化，用后或到期释放。
Linux 保留环境变量模式，不能用明文文件模拟钥匙串。

82 项 Python 测试使用合成凭据和隔离存储，涵盖目录默认值、无副作用读取、已有配置保留、
事务、信封边界、一次性/过期/上下文竞争及 RFC 7518 B.3 验证向量；32 项 JS 用例包括默认值与
自定义目录合并、WebCrypto 与独立 Node 密码算法互通、桥接只传
密文及加密不可用时拒绝提交。浏览器另需在 `connect-src 'none'` 条件验证保存，以覆盖
Codex 禁止页面访问本机 HTTP 的情况。macOS 原生解密、真实钥匙串及真实内嵌页面单独验收，
不能把模拟密钥或浏览器夹具通过视为这些层次通过，CI 不使用开发者钥匙串或真实账号。

`hosts/codex.py` 从本机解析默认标签和路径，`nacos_status.defaults` 只返回建议，不迁移已保存
配置。`.mcp.json` 明确透传 `CODEX_HOME`，不继承全部环境变量；安装默认个人 `.agents/skills`，
已有 `$CODEX_HOME/skills` 仅作为扫描候选。MCP 工作目录是插件安装目录，不是当前对话项目。
