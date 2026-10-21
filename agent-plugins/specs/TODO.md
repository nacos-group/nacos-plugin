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

# 通用路线图与适配分工

本文件记录跨 Agent 应用的功能方向和规范分工。完整功能编号 F01–F17 以
[功能规范](functional-spec.md)为准；各应用自行维护实现、待办、决策和验收结果，
一个适配通过验收不表示其他适配已经支持。

## 1. 通用演进方向

| 阶段 | 目标 | 通用约束 |
| --- | --- | --- |
| 基础接入 | Skill 生产与消费、显式双向更新、单中心接入、已有 MCP 与远端 Agent 消费、本地盘点。 | 区分资源读写、发布、应用加载和真实使用；保留来源、权限、冲突与恢复证据。 |
| 资源与治理扩展 | Prompt、AgentSpec、多中心、更多认证、企业配置与策略化更新。 | 模板按应用显式映射；后台进程与同步策略独立授权和验收。 |
| Agent 服务化 | 独立网关、隔离执行、任务映射、运行注册与活性。 | 不接管个人会话；注册成功不等于任务执行成功。 |
| 条件能力 | 资源中心页面、创建/更新提示。 | 页面由各应用实测决定；提示保留设计，是否实施另行评估。 |

## 2. 应用目录与实施入口

| 应用 | 源码与专属规范 | 当前状态 |
| --- | --- | --- |
| Codex | [源码](../codex/README.md)、[专属规范](../codex/specs/README.md)、[TODO](../codex/specs/TODO.md) | 开发预览；具体能力与剩余门槛见该适配记录。 |
| Qoder | 后续使用 `agent-plugins/qoder/` 与其 `specs/`。 | 尚无实现或兼容承诺。 |
| WorkBuddy | 后续使用 `agent-plugins/workbuddy/` 与其 `specs/`。 | 尚无实现或兼容承诺。 |

新增适配时先验证应用能力，建立独立的 manifest、安装路径、刷新方式、运行依赖、
测试和产物入口。通用业务契约继续维护在本目录，应用专属技术细节不得回写为所有应用的要求。

## 3. 状态与决策归属

- 资源身份、生命周期、治理、同步与通用验收原则变更：更新本目录对应规范。
- 应用 API、包格式、页面与事件机制、版本矩阵及实现选择：更新 `<agent>/specs/`。
- 现有 T01–T34、D01–D12 及开发预览状态归入 Codex TODO，保留编号以便追踪。
- 后续适配自行记录待办与证据；共用实现时明确源码来源，避免复制后产生语义差异。
- 私有测试环境配置、操作脚本和运行轨迹保存在仓库外，不进入 CI、文档或发布包。

## 4. UI 通用化基线

- [x] 将当前 SVG 的入口、菜单、步骤、条件冲突、确认、结果与返回整理为[通用操作规范](resource-center-interaction-spec.md)，以 UIX-01–UIX-14 供各应用引用。
- [x] 在[通用 UI 规范](resource-center-ui-spec.md)中明确行为、能力适配和视觉适配分工，样式尽量跟随所在 Agent 应用；Codex 图稿与通用操作建立映射。
- [ ] 后续新增应用时独立完成 UIX 能力清单、主题/组件映射及实际入口验收；Qoder、WorkBuddy 仍未实现。

本节完成的是设计归纳，不代表通用 UI 库或其他应用插件已经交付。
