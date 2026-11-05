# 规范迁移记录

2026-10-19 从 Nacos 设计 worktree 的未提交工作区复制 12 份 Markdown，保留原文件。
复制前后逐文件字节一致；排序后以文件名 UTF-8、NUL、原始文件字节、NUL 串联的 SHA-256：

`5910c5bfd0171717df882aa06e20cecaf458e44a865c90d03045d22fc6c1d135`

该摘要标识迁移输入快照，不是组件版本；迁移后有意更新链接、D01 与当前实施状态。
Nacos 源码契约锁定提交 `1511b5a85f744acb0ad54e8213b1f4d82674799c`，pom revision
为 `3.3.0-RC`。跨仓库引用锚定该提交，未复制整个 Nacos 规范库。
目标仓库迁移起点为 `51db264bb14bad9959df5737c884684871914775`。

保留 F01–F17、T01–T34（原有编号有意不连续）、D01–D12 的追踪方式。F16/T19 必做，
当时 F15/T18 条件交付，F17/T20 仅研究；这是迁移时的历史范围，后续计划以[全局路线图](../../specs/roadmap.md)为准。
本次不改根 POM、现有服务端模块或原 Java CI，也不提交、推送或发布。

同日按 Agent 应用重新组织目录：Codex 实现迁至 `agent-plugins/codex/`，manifest 与
内置 Skills 放在该目录根层；通用规范迁至 `agent-plugins/specs/`。Codex 的架构细节、
运行时选择、分发规则、可行性证据与 T/D 待办保存在 `codex/specs/`，共用规范只保留
跨应用契约及适配入口。原输入摘要继续标识最初的 12 份规范，不用于表示拆分后的文件集合。

2026-11-05 按用户要求合并通用 TODO、Codex TODO 中的未来计划和协作 roadmap，统一为
`agent-plugins/specs/roadmap.md`。Codex 历史事实迁入 `specs/implementation-status.md`，
Qoder 保留兼容/验收记录，各宿主不再维护独立路线图；稳定编号保留。
路线图按目标版本排列独立小功能；多 Agent 的组合架构、执行路径和结果契约迁入
`agent-plugins/specs/multi-agent-collaboration-spec.md`，原基线与论证章节不再保留在路线图中。
T20 调整为创建/修改后的默认发布询问，T21 补入使用前更新策略，新增 T35 多认证。
本次为规划与文档迁移，未改变功能代码或原验证结论。
