<!-- Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 -->

# 真实 Nacos 集成测试

测试启动独立 Nacos，使用真实认证、持久化、索引、审核及 Client/Admin HTTP API。
Codex、Qoder 分别在独立 Python 进程中运行自己的 Service、Registry 和 transport，
不注入 FakeRegistry，不替换 Nacos 的 HTTP 返回。

MCP/A2A 下游是本机 HTTP 测试服务；外部审核扫描器按合成标记返回通过/拒绝，Nacos 执行完整
Pipeline 并保存结果。这不验证第三方业务系统或扫描算法。真实应用页面、钥匙串弹窗、原生加载和
模型行为见[0.1.1 本地验收清单](../specs/0.1.1-local-acceptance.md)。

## CI 执行

[Agent plugin CI](../../.github/workflows/agent-plugin.yml) 的 build-integration-nacos 从
nacos-ref.txt 的完整提交构建公开 alibaba/nacos，不使用移动分支或 latest 镜像。
verify-nacos-integration 执行 **Codex/Qoder × 原生鉴权开启/关闭** 四个组合，使用 Java 17、Python 3.13。

每个组合使用随机空闲端口、临时 Derby 数据、随机测试密码和 JWT key、独立命名空间；
无需仓库 Secrets，不连接维护者实例。失败、启动超时或用例跳过均不能作为通过。
测试结束停止本次 Nacos、删除临时状态；保留环境摘要、结果与诊断日志，不上传数据库和配置。

原有 Ubuntu/macOS × Python 3.11/3.13 的自动测试及打包检查继续运行，Codex 页面状态测试仍由
Node 作业执行。Ubuntu 服务测试不表示 Linux 桌面或 Windows 插件已经兼容。

## 主功能覆盖

下表对应 test_registry.py 的实际测试方法；具体断言以代码为准。

| 功能 | 验证内容 |
| --- | --- |
| 认证和诊断 | 原生 login、Token、错误密码、匿名拒绝；鉴权关闭时验证 none；真实消费诊断。 |
| 盘点和生产 | 扫描/预览不上传、预检、上传草稿、内容核对、重复 apply 幂等、同名绑定与覆盖分别授权、登录身份的个人资源列表。 |
| FIX01 | 计划自读及另一客户端读取后，轮询确认 downloadCount 和版本 updateTime 已实际改变；内容未变，重启服务对象后原计划仍可上传。 |
| 上传冲突 | 本地文件、远端草稿、可见性和生命周期真实变化，拒绝写入并保留远端内容。 |
| 审核发布 | 草稿不能直接 publish；真实 Pipeline 通过后显式发布并消费读取；审核拒绝时阻止发布。 |
| 安装更新 | 指定版本安装、更新、本地修改保护、状态重载、核验、受管卸载与本地恢复。 |
| 远端撤回 | 安装计划生成后版本下线，执行时重新检查，不能仅使用缓存快照写入。 |
| 复用策略 | 免安装读取、ask/auto/never 核心规则、旧自动计划失效、重启持久化及明确安装例外。 |
| 上下文与权限 | 身份改变使旧计划失效，只读操作范围不能上传。 |
| 未知写结果 | Client/Admin 分别使用直连与转发地址；真实上传成功后截断响应，核对服务端草稿并 reconcile，断言上传只发送一次。 |
| 搜索 | Skill/MCP/Agent 跨类型搜索、类型筛选、cursor 分页不重复、真实命名空间隔离。 |
| MCP | 从 Nacos 发现端点、独立下游认证、工具枚举/调用、绑定与解除；握手不报告宿主已加载。 |
| A2A | 发现、免安装试用、绑定、发送、查询、取消、状态重载和解除；错误下游认证不能成功。 |

FIX01 必须观察统计和时间的落库变化，不能等待固定时间后直接报告成功。
异步检查有截止时间，超时失败；不会跳过不兼容接口来获得通过结果。
模型是否主动发现、原生连接是否加载属于本地清单，不由核心策略断言代替。

## 本地验证记录

2026-11-06 收尾复核：使用同一运行入口，在 macOS / Python 3.13.2 / JDK 17.0.8 上，
从公开 Nacos 提交 1511b5a85f744acb0ad54e8213b1f4d82674799c 构建发行包完成以下验证。

| 适配 | 原生鉴权 | 用例 | 失败 / 错误 / 跳过 |
| --- | --- | --- | --- |
| Codex | 开启 | 13 | 0 / 0 / 0 |
| Codex | 关闭 | 13 | 0 / 0 / 0 |
| Qoder | 开启 | 13 | 0 / 0 / 0 |
| Qoder | 关闭 | 13 | 0 / 0 / 0 |

四组共 52 项通过。这里只记录本机运行，GitHub Actions 的 Ubuntu 结果以对应 PR 工作流为准。
临时实例已停止并清理；原始日志保留在仓库外。上述结果不勾选本地宿主操作清单，
也不表示 0.1.1 已发布，候选包仍沿用当前源码的 0.1.0 版本号。

## 本地运行同一入口

需要 JDK 17、Maven、Python 3.11+ 及适配的 requirements-build.txt。
在独立的公开 Nacos checkout 中检出 nacos-ref.txt 指定提交，构建：

~~~sh
mvn -B -ntp -pl distribution -am install -Prelease-nacos \
  -Dmaven.test.skip=true -Dcheckstyle.skip=true -Drat.skip=true
~~~

从插件仓库根目录运行，替换发行包解压路径：

~~~sh
agent-plugins/codex/.venv/bin/python agent-plugins/integration/run.py \
  --nacos-home /path/to/nacos-distribution/nacos \
  --adapter all --auth enabled --output /tmp/agent-integration-enabled

agent-plugins/codex/.venv/bin/python agent-plugins/integration/run.py \
  --nacos-home /path/to/nacos-distribution/nacos \
  --adapter all --auth disabled --output /tmp/agent-integration-disabled
~~~

可以单独指定 codex 或 qoder，使用对应环境的 Python。
入口只接受发行包目录，不接受现有实例 URL；输出应位于仓库外。
查看各适配的 JSON 结果与同名日志。requestedNacosRevision 是要求的提交，
本地仍须核对输入包来源；CI 另外记录经过 checkout 校验的 ciSourceRevision。
