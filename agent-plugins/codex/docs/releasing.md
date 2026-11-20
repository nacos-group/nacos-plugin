<!-- Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 -->

# 发布 Codex 插件

Codex 与 Qoder 的 GitHub Release 统一遵循
[Agent Plugins 发布指南](https://github.com/nacos-group/nacos-plugin/blob/develop/agent-plugins/docs/releasing.md)。
指南包含版本与合并提交、干净构建、双端检查、八个附件、英文模板、草稿核对、正式发布和中断恢复。
这里使用仓库绝对链接，确保独立 Codex 安装包和源码包内也能访问。

Codex 专属的测试与构建命令见[开发指南](development.md)；支持范围见[兼容说明](compatibility.md)。
联合发布标题为 `Nacos AI Registry Agent Plugins <VERSION>`，组件 tag 为
`nacos-ai-registry-v<VERSION>`，本适配附件为安装 ZIP、源码 ZIP 及两份 SHA-256。
同一 Release 同时附上 Qoder 的四个文件，默认保持 `--latest=false`。

发行说明使用[统一英文模板](https://github.com/nacos-group/nacos-plugin/blob/develop/agent-plugins/release-notes/TEMPLATE.md)，
保留当次支持范围和人工待验项。GitHub Release 不等于 Codex 公开插件目录上架；
常规发布和升级保留配置，全新安装重置仅在用户明确要求时单独进行。
