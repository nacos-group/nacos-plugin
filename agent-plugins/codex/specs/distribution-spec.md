<!--
  Copyright 1999-2026 Alibaba Group Holding Ltd.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

# Codex 打包与分发规范

本文件补充[通用分发规范](../../specs/distribution-spec.md)。

## 1. 源码与产物标识

源码位于 `agent-plugins/codex/`，通用规范来自 `agent-plugins/specs/`。
插件身份保持 `nacos-ai-registry`，版本采用 SemVer，tag 为 `nacos-ai-registry-v<version>`；
安装包为 `nacos-ai-registry-<version>.zip`，源码包为 `nacos-ai-registry-<version>-source.zip`。
这些是 Codex 组件的标识，其他应用适配自行定义发布名称。

源码包保留 `codex/` 与 `specs/` 的相对层级，包含入口 README 和许可证，可脱离本仓库重建。
安装包根目录为可运行插件，附带同一来源的 `codex/` 源码与 `specs/` 通用规范，保证文档
链接和重建入口完整。marketplace 单独生成，不进入插件 ZIP。

## 2. 包结构与扩展声明

新包使用根目录 `plugin.json` 和可选的 `mcp.json`、`skills/`、`assets/`。
本地 MCP 的配置必须指向包内真实存在的构建入口。旧宿主需要兼容 manifest 时，保持
`.codex-plugin/plugin.json` 与根 manifest 的身份、版本和展示信息一致。

OpenAI 专有信息放在 portable manifest 的 `extensions.com.openai` 下。
打包检查应验证当前 schema、相对路径、manifest 引用、Skill frontmatter 与组件诊断，
不能仅验证 ZIP 可以解压。格式依据见
[官方打包说明](https://developers.openai.com/plugins/build/plugins)。

单个插件压缩包只包含该插件，不包含 marketplace 外层目录或其他插件。源码发布包与
安装包可以分别提供，二者不能混淆。许可证、依赖说明和必要运行文件随对应产物分发；
个人缓存、连接配置、token、私有资源和无关工作区文件不进入包。

页面构建产物与 MCP UI 资源声明必须一致，来自同一发布版本；本地包无需开发服务器即可
提供页面所需资源。UI 与工具的协议版本需兼容，升级后过期页面应刷新或重新打开。
单独记录工具可用、MCP Apps 页面可用和 Extension 入口可用的宿主矩阵，不将其中一项
测试结果外推到其他项。若采用远端托管页面，另行声明部署、网络和版本配套要求。

初始化工作流可通过 `extensions.com.openai.onboardingSkill` 声明；必须验证用户运行
setup 后能进入配置和盘点流程，而不是把声明字段当成安装后的自动执行回调。

自动提醒的 Hook 增强可按渠道生成独立构建变体，共享同一源码与核心：基础包不依赖 Hooks，
手动安装的桌面增强包才包含已验证的事件配置。含 Hooks 的包受当前公开目录限制；基础包
不含 Hooks 也不代表自动获得本地 MCP 的上架资格。增强包的 Hook 定义需要宿主信任，
升级改变定义后必须遵循宿主重新审查流程，不能绕过或替用户自动授予信任。

## 3. 公开目录的核对记录

截至 2026-10-19 的官方说明，本地 MCP 插件的公开目录提交限获准合作伙伴，并要求组织
白名单；含 lifecycle hooks 的插件包不能直接提交公开目录。此限制不等同于源码或自建
marketplace 不能对外分发。实际发布前必须重新核实准入和格式要求。
参见[桌面插件提交](https://developers.openai.com/plugins/deploy/desktop-only)和
[公开提交要求](https://developers.openai.com/plugins/deploy/submission)。


## 4. 构建与验收入口

构建与校验命令见开发指南（实现交付时见 `agent-plugins/codex/docs/development.md`），安装步骤见安装指南（实现交付时见 `agent-plugins/codex/docs/installation.md`）。
独立 CI 覆盖本目录和共享规范的变化，生成 Codex 产物；不调用 Maven，也不自动发布。
支持矩阵、页面门槛和其余验收项见 [TODO](TODO.md)。
