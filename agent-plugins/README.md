# Nacos AI Registry Agent Plugins

为 coding agent / personal agent 提供 Nacos AI Registry 接入，发现、管理和使用 agentic 资源。
各 Agent 应用的插件按目录独立维护，通用资源契约集中在 `specs/`。

```text
agent-plugins/
├── README.md
├── specs/                 # 通用功能、资源契约、治理与路线图
├── codex/                 # Codex 独立实现
│   ├── plugin.json
│   ├── mcp.json
│   ├── skills/
│   ├── src/
│   ├── tests/
│   ├── scripts/
│   ├── docs/
│   └── specs/             # Codex 适配、分发、验证与 TODO
└── qoder/                 # Qoder 适配源码与独立构建入口
    ├── .qoder-plugin/plugin.json
    ├── .mcp.json
    ├── skills/
    ├── src/nacos_qoder/
    ├── src/nacos_registry/
    ├── tests/
    ├── scripts/
    └── specs/             # Qoder 适配边界、待办与 compatibility.json
```

当前提供 Codex 和 Qoder 的开发预览源码；两者分别验证宿主能力，不共享宿主配置或用户状态。
Qoder 所需源码全部位于自身目录，运行、测试和构建不依赖 Codex 目录，
不包含 Codex manifest 或工作流。复用抽象后续单独处理；WorkBuddy 尚未声明支持。

| 阅读内容 | 入口 |
| --- | --- |
| 通用产品与功能设计 | [规范概览](specs/README.md) |
| 跨应用演进与分工 | [通用路线图](specs/TODO.md) |
| Codex 安装、开发与兼容范围 | [Codex 插件](codex/README.md) |
| Codex 实现与验收状态 | [Codex TODO](codex/specs/TODO.md) |
| Qoder 源码、安装与验证 | [Qoder 开发预览](#qoder-开发预览)、适配边界 `qoder/specs/README.md`、能力与兼容记录 `qoder/specs/compatibility.json` |

各适配独立构建和发布，不加入根 Maven 构建。插件源码、内置工作流与合成样例可以随包
交付；用户资源、凭据、私有测试环境配置及操作记录留在用户环境。

## Qoder 开发预览

`qoder/` 保留完整适配源码、Skills、测试、构建与包检查脚本，当前版本为 `0.1.0-dev.8`。
dev.7 按通用[能力发现规范](specs/capability-discovery-spec.md)补齐普通任务中的意图式发现：
新增入口技能 `nacos-find-capabilities`、`nacos_search` 引导文本与静态 MCP initialize 提示，
单轮预算为 3 次搜索各不超过 20 条（分页计入），最多比较 3 个候选；本地偏好 ask/auto/never
由插件状态单独保存，默认 ask，模型不得自行设为 auto，计划创建和落盘前各校验一次；
`nacos_preview_skill`、`nacos_mcp_trial`、`nacos_agent_trial` 提供免安装试用，不写技能目录也不留连接。
dev.8 修正询问形式的落点：`ask` 必须实际调用原生 `AskUserQuestion`，该要求同时出现在
入口技能正文、`status.discovery.askInterface`、三个试用结果的 `reuse` 和相关工具描述中，
`auto`/`never` 时不下发；此前该规则只在可选引用文件里，导致 dev.7 的一次真实会话用对话文字询问。
清单补齐展示元数据与自带图标 `assets/nacos-icon.png`，不引用其他适配目录。
dev.6 将下游用途明确为四项原生单选：“不使用”“接入 MCP”“调用远端 Agent”“都需要”，
不要求通过“其他”手动填写组合；“都需要”只涵盖本轮列出的能力，不自动注册或调用。
用户报告 dev.5 在另一会话完成初始化和简单发现，但该组合选项缺失；报告未独立核验，
不表示完整初始化、Keychain 生命周期或真实服务验收通过。
本版强化原生交互优先：API URL、自定义命名空间、目录和环境变量名也通过原生问答的
“其他”输入；只有工具未提供或实际不可用才说明原因并逐项降级，取消或拒绝不得绕过。
通用初始化及 ONB-02/03 验收同步约束此行为；秘密仍走独立系统安全录入。
旧 dev.4 已核验卸载、移除 MCP 及清理未配置状态；旧 dev.1–dev.4 本地分发产物按用户要求
清理，保留源码与历史验证记录。dev.8 安装后的实际发现触发、复用询问的原生渲染、同会话加载、
Keychain 和 Nacos 仍待验收。
宿主适配位于 `src/nacos_qoder/`，Nacos 协议、技能包校验、操作计划、冲突恢复及下游调用
源码位于本目录的 `src/nacos_registry/`。两者随安装包和源码包完整保留；从源码包的
`qoder/` 可独立重建，无需 Codex 目录、原仓库或 Maven。

当前开发预览已有单中心接入、技能搜索/上传/发布/安装/显式更新/恢复、本地盘点，以及已有
MCP 和 A2A 0.3.0 JSONRPC Agent 的发现与调用工具；dev.7 在 dev.6 的 26 个工具上新增
发现偏好与三个免安装试用工具，共 30 个，dev.8 维持 30 个，包括 `nacos_credentials`
本机安全录入/清除入口。
macOS 原生系统对话框与 Keychain 存储已实现，
但安装插件中的真实录入、真实 Keychain 读写及 Nacos 认证尚待用户验收；不表示首版全部通过。
同会话加载需用户在当前会话重新加载 Skills，或经原生连接器管理注册 MCP；插件没有刷新接口，
也不会自动重启应用，保存绑定、写文件或下游探针都不能当作宿主已加载的证据。
本版仍为对话工作流与 MCP 工具，未实现浏览器设置页、侧边页或资源中心。
兼容与能力记录 `qoder/specs/compatibility.json` 区分实现、隔离验证与真实环境验收。

### 首版范围与剩余门槛

通用规范基线为 develop 的 `5b30079`。首版采用[基础接入阶段](specs/TODO.md)：
单中心 Skill 生产与消费、显式双向更新、已有 MCP/远端 Agent 消费及可跳过的本地盘点。
新增的[初始化](specs/onboarding-spec.md)、[凭据管理](specs/credential-management-spec.md)、
[能力发现](specs/capability-discovery-spec.md)和[验收场景](specs/onboarding-acceptance-spec.md)适用于
Qoder，但不继承 Codex 的通过结论。

| 首版必须交付 | 当前情况与完成门槛 |
| --- | --- |
| F01 逐步初始化 | dev.6 下游用途四项原生单选含“都需要”；沿用 dev.5 原生交互优先，枚举单/多选，自定义非敏感值通过 Other 每轮收集一个；只在工具未提供/实际不可用时说明原因降级，拒绝或取消不绕过，已有值不重问。none/login/token 与凭据来源分开，本机 macOS 推荐 keychain，environment 仅高级备用；默认命名空间（ID public）不是“公开”，缺凭据不诊断。155 项本地回归含原生输入规则及 URL 问答示例通过；dev.4 截图显示首个 URL 步骤退回聊天，dev.5 安装后的实际渲染/取消/完整引导仍待验收。 |
| F01/F14 配置与诊断 | 保存必填 expectedRevision 拒绝并发/迟到覆盖；诊断独立保存当前上下文、状态、时间和固定错误。最新状态上下文含私有随机密钥对当前 Keychain 载荷及环境值的 HMAC，轮换、移除或拒绝访问使旧上下文、计划及诊断失效；中断不报通过。dev.4 绑定失败、上下文变更及 Keychain 支撑的模拟 login/diagnose 已本地验证，真实宿主/存储/Nacos 待验收。 |
| F01/F11 凭据边界 | nacos_credentials 只接收 action enter/clear、surface client/admin 及必填 _context，不接收任何明文秘密参数。本机 osascript 对话框录入，密码/Token 隐藏，用户名仅在系统对话框可见；绑定变更丢弃引用并要求重新录入，Keychain 不支持 authorizeCredentialReuse。共享 Client/Admin 录入一次，独立配置分别录入；55 项凭据测试通过，含 fake SecItem 查询标志/错误映射及下游别名隔离，未访问真实 Keychain/Nacos。 |
| F02/F03/F04 Skill 闭环 | 搜索、上传预检、草稿、提交/发布、确切版本读取和安装已有工具。仍需真实 Nacos 审核/可见性验收，以及 Qoder 用户/项目作用域的发现和实际使用验证。 |
| CD 能力发现与复用 | dev.7 已实现入口技能、工具引导文本、静态 initialize 提示、单轮预算、ask/auto/never 偏好的双重校验，以及免安装预览与 MCP/Agent 试用的分页和限额；发现、可达、已保存、宿主已加载、本轮可调用与实际使用分开陈述。dev.8 把“`ask` 必须实际调用原生 `AskUserQuestion`”写入入口技能正文、状态和试用结果，修正了 dev.7 真实会话中退回对话文字的问题。13 项专项测试在 171 项套件内通过，使用假 HTTP 与合成包。真实新会话的发现触发、询问渲染、同会话 Skill 重载与原生连接器加载仍待验收。 |
| F10/F16 显式更新与盘点 | 保留已有盘点结果或继续当前选择，不自动重复扫描；选择须针对当前扫描，全部可读候选有选择才允许完成，终态才能 reopen。稳定选择和 rootStates 保留；普通设置变更保留归属但旧写计划失效，未知结果不自动重发，不提供后台同步。 |
| F07/F08 MCP 与远端 Agent | MCP 绑定不等于原生注册，仍需另行确认注册/移除并核验工具使用。Agent 绑定拒绝并发覆盖；下游凭据更换须重新绑定，已知任务仅能在重新授权的原端点继续。本地回归及下游别名隔离测试通过；A2A 限定 0.3.0 JSONRPC，真实 send/get/cancel 验收待完成，不承诺流式。 |
| F12/F13/F14 源码与交付 | dev.8 完整源码保留，171 项 checkout 测试（82 适配/核心、58 凭据、18 分发、13 发现与加载）及实际解压源码 ZIP 的全部测试通过；包/校验和/清单展示与图标断言、隔离 zipapp CLI/stdio 及源码与安装包内源码字节一致离线重建通过，无 Codex 源码差异。CLI 严格校验沿用历史 dev.6 结论，未对 dev.7/dev.8 重跑。原生安装、升级、配置后卸载/凭据清理仍待验收，不宣称 Qoder 全链路通过。 |

**普通用户凭据入口（本地模拟验证通过，真实验收待完成）**：本机 macOS 优先使用系统对话框与
Keychain，不要求把账号密码或 Token 发到聊天、工具参数、仓库或宿主 MCP 配置。保存/清除
无需重启；环境变量可能需重启，仅在安全录入不可用或用户主动选择时作为高级回退，绝不
作为普通用户推荐路径。本地 Qoder 进程的系统对话框可用性探测已完成并超时干净退出；这不是
已安装插件的秘密录入或真实 Keychain 测试，也不证明真实 Nacos 认证成功，均需用户测试。
未实现浏览器设置页、侧边页、资源中心或 MCP 加密信封。

**后续或条件能力**：完整 F15 资源中心、Prompt、AgentSpec、多中心、企业策略与后台更新、
本地 Agent 网关/服务化、F17 创建/更新提示，以及跨插件共享抽象。Linux 待验证且不能宣称
支持 macOS 凭据入口，Windows 尚不支持；无页面的 UIX 和页面专属分支不适用，不是通过。
Keychain 生命周期及系统对话框取消/失败边界已纳入 CRED 映射，验收仍待完成。

ONB-01–ONB-08、CRED-01–CRED-10、DEF-01–DEF-06 的逐项映射及未通过项保存在
兼容记录 `qoder/specs/compatibility.json`；真实宿主、真实 Nacos、系统存储和隔离测试分层记录。

### 构建和验证

本机运行需要 Python 3.11+，构建时安装锁定的 PyYAML 6.0.3；安装产物内置纯 Python
PyYAML，使用者不需要 pip、Node.js 或 Java。Windows 因本地状态锁使用 `fcntl` 暂不支持，
Linux 尚未实测。以下命令从仓库根目录执行：

```sh
python3 -m venv agent-plugins/qoder/.venv
agent-plugins/qoder/.venv/bin/python -m pip install -r agent-plugins/qoder/requirements-build.txt
PYTHONPATH=agent-plugins/qoder/src agent-plugins/qoder/.venv/bin/python -m unittest discover -s agent-plugins/qoder/tests -v
agent-plugins/qoder/.venv/bin/python agent-plugins/qoder/scripts/build.py
agent-plugins/qoder/.venv/bin/python agent-plugins/qoder/scripts/check_package.py
qodercli plugins validate agent-plugins/qoder/dist/nacos-ai-registry --strict --json
```

从源码 ZIP 重建时，在解压根目录执行 `python3 -I -S -B qoder/scripts/build.py` 和
`python3 -I -S -B qoder/scripts/check_package.py`；内置 PyYAML 源码，无需 pip 或其他插件。
源码测试可使用 `PYTHONPATH=qoder/src:qoder/vendor/pyyaml python3 -S -B -m unittest discover -s qoder/tests -v`。
`qoder/dist/` 生成安装 ZIP、源码 ZIP、对应 SHA-256 和展开插件目录。本版 ZIP 命名为
`nacos-ai-registry-qoder-0.1.0-dev.8.zip` 与 `nacos-ai-registry-qoder-0.1.0-dev.8-source.zip`；
只上传前者。构建信息记录来源摘要、基线提交、工作区是否有未提交改动和依赖版本。
生成产物被 Git 忽略，维护者应提交源码，不把构建包或私有配置提交到仓库。
**dev.8 本地验证（2026-10-27）**：171 项 checkout 测试通过（82 适配/核心、58 凭据、
18 分发、13 发现与加载），覆盖发现偏好默认值、持久化与原生询问要求、计划与落盘两次
复用校验、三个免安装试用及其分页/限额和随偏好变化的复用提示、下游凭据隔离、入口技能
契约、静态 initialize 提示、加载阶段与原生连接名称迁移。实际解压的 dev.8 源码 ZIP 以
Python 3.13 `-S -B`、仅内置 YAML、空 HOME 且无 Codex 目录运行，171 项全部通过。
`build.py` 与 `check_package.py` 通过校验和、ZIP 元数据、完整源码、清单展示与图标断言、
隔离 zipapp CLI 及 initialize/tools-list/status，源码与安装包内源码离线重建字节一致；
`*.zip.sha256` 已验证，无 Codex 源码差异。CLI 严格校验沿用历史 dev.6 结论，本版未重跑。
真实新会话的发现触发、复用询问的原生渲染、同会话 Skill 重载、原生连接器加载、真实
Keychain 与 Nacos 仍待用户验收。
**历史 dev.7 本地验证（2026-10-27）**：同样 171 项 checkout 测试、解压源码测试、包与
校验和检查及离线重建通过；其复用询问在真实会话中退回对话文字，由 dev.8 修正。
**历史 dev.3 验证**：`0.1.0-dev.3` 通过 100 项测试（82 项适配/核心与 18 项分发契约）；
实际源码 ZIP 在禁用 site packages、仅使用内置 YAML 且没有 Codex 目录的隔离环境中也
通过全部 100 项；当时安装/源码 ZIP 校验、离线重建字节一致性和 CLI 严格格式校验通过。
**历史 dev.6 本地验证（2026-10-26）**：155 项 checkout 和实际解压源码 ZIP 测试通过，
包括四项下游单选 JSON 示例、“都需要”及权限合并/未来能力边界断言。完整源码、校验和、
ZIP 元数据、隔离 CLI/stdio、源码与安装包内源码字节一致重建通过；CLI 1.1.46 严格校验
零错误/警告。已通过官方入口从 dev.5 原地升级至 dev.6：安装内容逐文件与最终 ZIP 一致，
安装后 runtime initialize 返回 dev.6、26 个工具及已有配置；Desktop MCP 已重新就绪且 status
读取成功。升级前后本地状态和两处已有用户技能字节一致，配置修订仍为 4，共用钥匙串凭据
状态仍为 ready；未重新录入、删除凭据或访问真实 Nacos。本次验证不等于钥匙串完整生命周期
或实际问答渲染通过；分发包内兼容记录的安装 pending 是打包前快照，升级后证据记录于此。
**历史 dev.5 本地验证（2026-10-26）**：155 项 checkout 回归（82 适配/核心、55 凭据、18 分发）
及实际源码 ZIP 在空 HOME、禁用 site packages、仅内置 YAML 且无 Codex 目录下的全部测试通过。
包含原生交互优先规则与首次 URL 问答 JSON 示例断言。构建/包检查、校验和、完整源码与
ZIP 元数据、隔离 zipapp CLI/stdio、源码和安装包内源码字节一致离线重建均通过；CLI 1.1.46
严格校验零错误/警告，Codex 未修改。安装后的实际原生问答、系统凭据录入/Keychain、真实
Nacos 与有配置/资源的卸载清理仍待验收，本地通过不代表全链路通过。
**历史 dev.4 本地验证（2026-10-26）**：已完成全部 155 项测试（82 项适配/核心、
55 项凭据、18 项分发契约），全部通过。凭据测试含 fake SecItem 查询标志/错误映射、
Keychain 支撑的模拟 login/diagnose、绑定失败与上下文变更、下游别名隔离及归属条目
清除/重试。实际解压的 dev.4 源码 ZIP 以 `python -S -B`、仅内置 YAML、空 HOME 且
无 Codex 目录运行，全部 155 项也通过。`build.py` 与 `check_package.py` 已通过校验和、
ZIP 元数据、完整源码、隔离 zipapp CLI 及 initialize/tools-list/status 检查；源码和安装包内
源码离线重建均与安装/源码 ZIP 及 runtime 字节一致。生成的 `*.zip.sha256` 文件已验证；
不在源码文档中嵌入确切 ZIP 哈希，以免形成哈希循环。`qodercli` 1.1.46 严格校验为零错误、
零警告；无 Codex 源码差异。文档输入同样纳入分发与离线重建检查。
所有秘密测试仅用 fake 存储/对话框及合成值，无真实用户秘密、实际 Keychain 或真实 Nacos；
这些本地通过不替代 dev.4 Desktop 安装、真实对话框/Keychain/Nacos 或原生连接器验收。

### 安装与初始化

Desktop：在 **Extensions → Plugins → Add Plugins → Upload Plugin** 选择安装 ZIP，
启用插件并打开本地会话，发送“初始化 Nacos AI Registry，先调用 nacos_status”。
ZIP 根包含 `.qoder-plugin/plugin.json`，MCP 路径使用 `${QODER_PLUGIN_ROOT}`。
本机 CLI 1.1.46 的历史 dev.4 严格格式校验（零错误/警告）、隔离 zipapp 工具启动及源码重建
已通过，历史结果仍按版本保留在兼容文件。Desktop 在 `0.1.0-dev.2` 曾发现 25 个工具并读取未配置状态，初始化却
返回批量字段清单；用户在另一会话报告 dev.3 分步原生选项可用，但命名空间措辞及仅环境变量
体验失败，该报告未独立核验。dev.4 已实际发现 26 个工具并读取未配置状态，但用户截图显示
首个 URL 步骤退回聊天询问；卸载与空状态清理已核验，不证明完整初始化或真实 Keychain。
dev.5 修正自定义输入路径，须安装后新建本地会话验证首个 URL 的原生 Other 输入、原生选项、
取消/降级边界、本机安全录入、Keychain 和真实业务。
dev.8 另需在普通任务中验证发现是否被触发或被正确跳过、`ask` 偏好是否真正发出原生询问
（dev.7 在此处退回了对话文字），以及同会话的 Skill 重载与原生连接器加载；插件没有刷新接口，
也不会自动重启应用。
dev.2 未配置环境的原生卸载、MCP 移除及专用空状态/孤立缓存清理已核验，保留用户技能、
其他插件、远端资源、完整源码与当时 dev.3 归档；不代表配置后 Keychain 清理已通过。
CLI 的实际会话调用仍因 SDK 认证载荷缺失未完成；完整升级、带用户资源的卸载及真实
Nacos/Skill/下游使用验收仍待完成。
CLI 本地安装与开发临时加载入口已通过 `--help` 核实，分别使用：

```sh
qodercli plugins install ./agent-plugins/qoder/dist/nacos-ai-registry
qodercli --plugin-dir ./agent-plugins/qoder/dist/nacos-ai-registry
```

这些命令基于本机 `qodercli --help`，其他版本先核对实际命令；不要照搬 Codex marketplace。
安装会变更插件配置，临时加载不代替正式安装。源码目录不含生成 runtime，先构建后加载。
升级重新构建并通过宿主安装/更新入口执行，不直接编辑缓存；卸载插件与清理托管技能、
原生连接器分别选择，均不自动删除 Nacos 资源。
`0.1.0-dev.8` 安装或升级后新建本地会话并重新发现工具 schema，先调用 `nacos_status`；
保存配置必须传最新 `configurationRevision` 作为 `expectedRevision`。已有 schemaVersion 1
状态保留；旧版本写计划须重新生成，已有下游绑定须重新授权，不自动执行迁移中的远端写入。
发现偏好单独保存，默认为 `ask`，升级既不沿用其他取值也不改写已保存的选择；dev.6 已保存的
MCP 绑定保留旧的 `nacos_<20 位十六进制>` 连接名，只有在用户确认后才迁移到新的名称格式。

默认技能目录为 `~/.qoder/skills`，项目作用域使用用户明确选择的 `<workspace>/.qoder/skills`；
MCP 从插件目录启动，不能据其 cwd 推断工作区。插件状态独立保存到
`~/.qoder/state/nacos-ai-registry`，可由 `NACOS_QODER_HOME` 指定，不读取 Codex 的
`NACOS_PLUGIN_HOME`。Nacos 默认命名空间显示为 **默认命名空间（ID public）**，
不能把 ID `public` 解释为公开可见性。

认证协议为 `none`、`login` 或 `token`，与凭据来源分开选择。profile auth 的
`source: keychain` 是本机 macOS 推荐路径；`source: environment` 仅在安全录入不可用或
用户主动选择时作为高级回退，绝不推荐普通用户使用。环境分支只存变量名，值须对实际
MCP 进程可见，可能需重启；不能发到聊天、写入仓库或宿主 MCP 管理配置。
`credentialStatus.ready` 只表示当前凭据可读取，不证明 Nacos 接受；缺失、拒绝访问或
不可用均不得降级匿名。保存配置不连接服务，另行用只读 diagnose 核验。

`nacos_credentials` 参数仅为 `action: enter|clear`、`surface: client|admin` 及必填
最新 `_context`；没有用户名、密码、Token 或其他明文秘密参数。`enter` 通过本机
`osascript` 打开系统对话框：密码/Token 隐藏输入，用户名仅在系统对话框可见，不进入
模型、工具参数或结果。共享 Client/Admin 只需录入一次，独立配置分别录入。Keychain
使用 SecItem generic password，service 为 `io.nacos.ai-registry.qoder.<state root hash>`，
不启用同步；profile 只存不透明 `credentialRef`。条目绑定连接 ID、身份、目标、认证
类型及用途（共享或独立）；配置修改若改变绑定，丢弃引用并要求重新录入。Keychain
不支持 `authorizeCredentialReuse`，不能通过授权把旧条目带到新目标；环境分支的目标
复用授权与下游服务认证仍分别管理。

凭据事务先把新引用记入 journal，再保存 Keychain 条目并原子保存 profile。若 fsync
失败，回滚先核对 profile 是否已持久化；失败保存后内存重新加载持久状态，只有配置持久
保存后才删除旧归属条目。拒绝删除时保留清理 journal，`cleanupPending` 在 status 及
credential/configure 结果中可见，后续 configure/credentials 操作重试。上述模拟故障、
归属条目清除/重试已本地验证；CRED-10 配置后卸载与完整清理验收仍有限/待完成。
保存/清除立即生效，无需重启；真实系统拒绝权限、故障回滚和清理仍待验收。

本地 `.credential-key` 是私有随机授权指纹密钥，不保存账号密码，也不是系统凭据库；
目录/密钥要求当前用户所有及 0700/0600 权限，异常时拒绝访问而不自动替换，不进入分发包。
最新 status 上下文包含该密钥对当前 Keychain 载荷和环境值的 HMAC，不保存秘密；轮换、
移除或拒绝读取凭据使旧上下文、写计划和诊断失效。dev.4 绑定失败及上下文变更已在 fake
存储/合成凭据测试中验证；真实 Keychain、宿主新会话/重启及 Nacos 验收仍待完成。

MCP 接入先保存本地绑定，再通过 Qoder 原生连接器管理完成另行确认的注册；插件不会
直接写 `settings.json`。bearer 引用只供插件探测，宿主认证须使用受支持的安全入口；不把
秘密传给 `manage_mcp.config`。本地绑定、原生工具加载和实际使用分别核验。技能文件写入
同样不代表宿主已发现；在新本地会话中验证可见性和实际使用。当前隔离测试不等于真实
Nacos 服务或 Desktop 页面已完成验收。
