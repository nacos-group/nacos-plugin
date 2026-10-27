# Nacos AI Registry Agent Plugins

让你使用的 AI 助手接入 Nacos AI Registry，在对话中发现、使用和管理团队共享的能力。
这些插件安装在 Codex、Qoder 等 Agent 应用中，使用已经部署好的 Nacos 服务。

团队可以在 Nacos 中维护三类常用资源：**Skill** 是可复用的操作说明和工作流程，
**MCP** 提供工具调用，**远端 Agent** 接收任务并返回结果。插件负责搜索资源、准备使用环境、
保存本地连接，以及管理技能的版本和发布；Nacos 与下游服务继续负责访问权限。

比如，你可以说“找一个能查询内部系统的工具”，也可以直接提出业务需求。支持意图发现的插件会在
缺少合适能力时尝试搜索，是否采用找到的资源仍由模型根据任务判断。资源发现与长期安装分开，
避免每次查询都往本地添加不需要的技能或连接。

## 当前插件与版本

下表对应**当前分支中的源码**，不代表同名版本已发布到 Release 或应用插件目录。
各子插件独立版本、独立构建；实际下载版本以 Release 附件为准。

| 应用 | 源码版本 | 已实现功能概览 | 使用与兼容入口 |
| --- | --- | --- | --- |
| Codex | **0.1.0** | 逐步初始化；macOS 页面录入凭据；Skill 搜索、上传、发布、安装、更新、恢复与卸载；MCP/Agent 发现与使用；意图发现、免安装试用和三种复用策略；资源中心页面。 | [安装与开发](codex/README.md)、[兼容范围](codex/docs/compatibility.md)、[待办](codex/specs/TODO.md)。 |
| Qoder | **0.1.0** | 原生问答初始化；macOS 系统对话框与钥匙串；Skill 生产消费、显式更新与本地盘点；MCP/Agent 发现与使用；意图发现、免安装试用及交互式复用询问。当前为对话与工具工作流。 | [Qoder 使用与开发](#qoder-使用与开发)。页面未实现；同会话加载依赖应用原生重载与连接器能力，尚待实际验收。 |
| WorkBuddy | 尚未实现 | 预留适配方向，暂无可安装产物。 | 后续在 `workbuddy/` 独立实现。 |

“已实现”表示代码具备相应能力；操作系统、应用版本和真实服务的验证范围由各子插件单独记录。
两套实现使用各自的配置和状态，安装一个不会替另一个完成配置，也不自动共享凭据。

## 目录结构

```text
agent-plugins/
├── README.md                 # 目的、版本、能力概览与开发原则
├── specs/                    # 跨应用的资源、交互、凭据及治理规范
│   └── platforms/            # 可复用的操作系统实现约束
├── codex/                    # Codex manifest、工作流、源码、测试和构建
│   ├── README.md
│   ├── docs/
│   └── specs/                # Codex API、UI、兼容与验收映射
└── qoder/                    # Qoder 的独立实现、工作流、测试和构建
    └── specs/                # 适配边界、兼容矩阵及开发预览记录
```

每个适配应能独立运行和构建，不依赖另一个插件目录或根 Maven 构建。目前两套插件各自维护
实现；共享规范不意味着已经有一个跨应用公共运行库。真正需要共享代码时，再明确模块依赖、
兼容范围和独立打包方式。

## 开发原则

1. **先定义行为，再做应用映射。** 从[通用规范](specs/README.md)确认资源身份、权限、生命周期、
   发现和复用行为。跨应用都应遵守的规则放在 `specs/`；应用 API、配置格式、路径、工具名、
   UI 主题和验证结论放在 `<agent>/specs/`，通过引用关联，避免重复定义。
2. **顺着所在应用的使用方式实现。** 能用原生交互式选项就用原生选项；页面尽量跟随应用本身的
   风格。支持什么、不支持什么要明确，不能把 Codex 的接口、SVG 或验收结果直接当作其他应用的支持。
3. **把使用和持久变更分开。** 搜索不等于安装，试用不等于保存，文件写入不等于应用已加载。
   写入走计划、校验和应用流程，保留来源、用户修改与恢复信息；隐式发现按[复用策略](specs/capability-discovery-spec.md)处理，
   用户明确要求安装时按该请求执行。
4. **保护连接和用户数据。** 认证遵循[凭据规范](specs/credential-management-spec.md)，注册中心与下游
   服务的凭据分别处理。升级保持既有配置和资源归属；卸载插件、删除配置、移除用户资源是不同动作。
5. **分别验证实现和实际使用。** 维护单元/协议测试、打包检查和应用内验收记录。合成测试通过不能
   代替真实应用加载和任务执行；未验证的分支留在对应适配的 TODO 中。
6. **独立构建、可追溯分发。** 每个插件自行维护版本、manifest、构建入口、产物名和依赖，遵循
   [分发规范](specs/distribution-spec.md)。安装包与源码包来自同一份源码；不要手工改安装缓存或生成产物。
7. **私有环境留在仓库外。** 只提交源码、文档和合成测试样例。真实地址、账号、凭据、业务资源和
   联调操作记录不进入仓库、CI 或发布包。

新增适配时，先核验应用的插件入口、运行方式、技能目录、凭据输入和加载/刷新能力，再建立独立目录，
记录通用规范的采用范围与缺口。提交改动时一并更新本页的版本/能力概览及受影响适配的测试说明。

## 进一步阅读

- [通用规范导航](specs/README.md)：初始化、凭据、发现、装配、UI 和分发。
- [通用路线图](specs/TODO.md)：跨应用目标与适配分工。
- [Codex 使用与开发](codex/README.md)：两种安装方式、源码运行、测试与发布入口。
- [Qoder 使用与开发](#qoder-使用与开发)：桌面导入、qodercli 安装、源码结构与构建入口。

## Qoder 使用与开发

Qoder 的安装入口、初始化步骤、源码结构和构建命令集中在
[Qoder 插件 README](https://github.com/nacos-group/nacos-plugin/blob/develop/agent-plugins/qoder/README.md)。
桌面端在 **Extensions → Plugins → Add Plugins → Upload Plugin** 选择安装 ZIP；也可用
`qodercli plugins install <插件目录>` 安装已展开的插件目录（当前 CLI 不接受本地 ZIP 路径）。
安装后在本地会话先调用 `nacos_status`，再用 `nacos-setup` 完成原生分步初始化。
从源码构建时在 `agent-plugins/qoder/` 执行测试、`scripts/build.py` 与 `scripts/check_package.py`，
产物生成在该目录的 `dist/`；仓库 CI 的 `verify-qoder` 作业在 ubuntu/macOS 与 Python 3.11/3.13 上重复这一流程。

| 内容 | 入口 |
| --- | --- |
| 安装、初始化、源码结构与构建 | [qoder/README.md](https://github.com/nacos-group/nacos-plugin/blob/develop/agent-plugins/qoder/README.md) |
| 适配边界与通用规范映射 | [qoder/specs/README.md](https://github.com/nacos-group/nacos-plugin/blob/develop/agent-plugins/qoder/specs/README.md) |
| 兼容矩阵与逐项验收证据 | [qoder/specs/compatibility.json](https://github.com/nacos-group/nacos-plugin/blob/develop/agent-plugins/qoder/specs/compatibility.json) |
| 历史开发预览与逐版本验证记录 | [qoder/specs/development-preview.md](https://github.com/nacos-group/nacos-plugin/blob/develop/agent-plugins/qoder/specs/development-preview.md) |

在源码仓库中这些文件位于 `qoder/`；独立插件包不附带其他应用的实现。`0.1.0` 的适配内容与
开发预览 `0.1.0-dev.8` 一致，只增加了版本号和 CI 覆盖，验收边界不因去掉 dev 后缀而放宽：
真实会话的发现触发、原生询问渲染、同会话 Skill 重载、真实钥匙串与 Nacos 以兼容矩阵的记录为准。
