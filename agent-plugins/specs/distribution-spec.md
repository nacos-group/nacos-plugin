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

# 打包与分发规范

本文约束 F12、F13，定义源码、宿主安装包及分发渠道的边界。目录归属和发布平台的选择
不改变核心资源契约；具体实施选择记录在 [TODO](TODO.md)。

## 1. 源码与构建产物

同一个源码版本必须能够构建对应的发布包。源码至少包括共享核心、宿主适配器、内置
工作流、页面源码与静态资源、验证用例、构建/打包流程和兼容说明。可选 Agent 网关作为独立运行产物交付，
不能隐藏在插件安装过程里启动。

每个发布记录源码提交、插件版本、构建方式、依赖锁定信息、支持矩阵、包摘要和变更说明。
插件使用独立版本号；它不等同于 Nacos Server 版本，也不等同于下载资源的业务版本。
多个宿主可以生成不同包，但共享核心的来源必须可追溯。

源码归属 `nacos-group/nacos-plugin/agent-plugins/`，按应用组织为 `<agent>/`。
通用规范在 `specs/`，应用专属规范在 `<agent>/specs/`；例如 `codex/`，未来可增加
`qoder/`、`workbuddy/`。各适配独立声明版本、发布 tag 和产物名，不沿用服务端插件与
Nacos 版本一一对应的规则。独立 CI 执行相应适配的测试与打包，不增加 Maven 必需依赖。

| 产物 | 内容 |
| --- | --- |
| 源码 | 实现、工作流、设计、验证及构建说明。 |
| 宿主插件包 | manifest、内置 Skills/资源、连接描述和运行所需文件。 |
| 可选运行依赖 | 有明确版本和安装方式的运行时或平台产物。 |
| 可选网关包 | 服务配置模板、执行适配器、部署与运维说明。 |
| 分发目录 | 指向发布版本的 marketplace/catalog 信息，独立于单插件压缩包。 |

包不能依赖维护者的绝对路径、源码工作区、临时构建目录或个人凭据。运行时依赖必须被
明确声明并验证，或以允许的方式构建到分发产物中；不能假设每位员工都已安装开发工具链。

## 2. 各应用的包格式

每种 Agent 应用的 manifest、工作流入口、运行连接和可选 UI/事件扩展，在其目录下
单独定义与验证。各发布包只包含该插件所需内容，构建不能把整个 `agent-plugins/` 下的
其他适配一并打入产物。通用规范与相应应用的规范可以随包提供，并保持相对链接有效。

格式和渠道要求参见各应用规范，当前入口为 [Codex 打包与分发](../codex/specs/distribution-spec.md)。
具体平台的上架规则不能外推到其他应用。

声明页面能力时，页面产物与工具/UI 资源声明来自同一发布版本，协议需兼容；升级后的
过期页面应刷新或重新打开。本地包应能脱离开发服务器提供页面；远端托管页面须单独说明
部署、网络及版本配套。工具发现、页面可用与固定入口可用分别验收，不能互相替代。

## 3. 安装、升级与卸载

安装流程必须完成宿主与运行依赖检查、插件启动、工具发现以及一次无副作用的验证调用。
账户中的插件记录创建成功，不表示运行服务已部署或本地工具已经加载。

插件升级从分发源和源码目录构建新的包，通过宿主支持的重装/升级流程生效，不直接修改
宿主的插件缓存。升级必须保持用户 profile、托管安装记录和已锁定资源版本，必要时执行
可恢复的数据格式迁移。

卸载插件与清理用户资源分别处理。卸载不自动删除 Nacos 资源；本地已下载资源按归属、
依赖和用户选择清理。已部署的网关若仍提供服务，需要明确的停止与注销流程。

凭据升级保留与显式配置清理遵循[凭据生命周期](credential-management-spec.md#4-保存替换与清除)；
清理插件配置不隐含删除本地 Skill，也不隐含已成功清除系统拒绝删除的凭据。

## 4. 分发渠道

| 渠道 | 适用方式 | 前置条件 |
| --- | --- | --- |
| 个人本地安装 | 本地源码构建后测试，或安装已构建包。 | 宿主支持本地安装且运行依赖可用。 |
| 团队或外部分发 | 发布源码、Release 包和本地/Git marketplace 入口。 | 使用者可访问分发源，并按支持的宿主流程安装。 |
| 工作区共享 | 按所在平台的工作区插件机制共享。 | 管理员权限、组织策略及运行环境允许。 |
| 官方公开目录 | 单独准备审核材料、演示与支持信息，提交审核。 | 满足当时的目录准入要求，不由普通包构建自动获得资格。 |

## 5. 验收重点

从干净环境验证下载、安装、启动、配置入口、工具发现、升级和卸载；声明支持图形界面
时，还须验证包内页面加载、桥接调用、重新进入与升级后的状态恢复。检查 macOS、Windows、
Linux 等所声明平台上的运行依赖；未经验证的平台不得列为支持。发布包扫描应覆盖秘密、
绝对路径、缺失引用、版本不一致、源码与产物不对应和非预期可执行内容。
