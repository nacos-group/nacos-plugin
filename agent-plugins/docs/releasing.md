<!-- Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 -->

# Agent Plugins 发布指南

Codex、Qoder 共用本流程，分别构建，再放进同一个 GitHub Release。本文记录 0.1.1 实际采用的
命名、说明风格、附件和核对步骤；后续版本更新参数及当次验证结果，不复制旧版本的通过结论。
GitHub Release 与宿主公开插件目录上架是两项操作。

## 1. 固定约定

| 项目 | 约定 |
| --- | --- |
| 仓库 | `nacos-group/nacos-plugin` |
| 标题 | `Nacos AI Registry Agent Plugins <VERSION>` |
| Tag | `nacos-ai-registry-v<VERSION>`，annotated tag，指向确定的合并提交 |
| 版本 | 两宿主版本一致，来自同一个干净提交；未来独立发版须先调整本流程和检查器 |
| 稳定版 / 预发布 | 稳定版不标记 Pre-release；`-dev.*`、`-rc.*` 等后缀版本标记 Pre-release |
| Latest | 创建和发布都指定 `--latest=false`；需要改变服务端插件的 Latest 展示时另行明确 |
| 附件 | 恰好 4 个 ZIP 和对应的 4 个 `.zip.sha256`；明确列文件名，不上传整个 `dist/*` |
| 说明 | 英文，使用[模板](../release-notes/TEMPLATE.md)，保留升级、支持范围和待验项 |
| 发布顺序 | 干净构建 → 本地验证 → tag → 草稿 → 远端附件核对 → 发布 → 回读核对 |

早期 `ap-0.1.0` 是历史命名，不重命名旧 tag，也不改写已发布 tag 或替换已发布附件。

## 2. 版本与源码准备

先完成版本 PR 并合并，核对版本声明、README 和相应验收记录：

| 宿主 | 版本声明 |
| --- | --- |
| Codex | `codex/plugin.json`、`codex/src/nacos_registry/__init__.py` |
| Qoder | `qoder/.qoder-plugin/plugin.json`、`qoder/src/nacos_qoder/__init__.py`、`qoder/src/nacos_registry/__init__.py` |
| 兼容记录 | `qoder/specs/compatibility.json` 的当前版本；历史版本保持原值 |

Plugin 版本不跟随根 Maven/Nacos Server 版本。不要改安装缓存、改名旧 ZIP 或修改已发布包中的版本字符串。
主工作区有未提交内容时保留它们，使用独立工作树，不能带入发布目录。

下面命令在**同一个 Bash 会话**执行，从仓库根目录开始；替换所有尖括号占位符。
`RELEASE_COMMIT` 是完整 40 位合并提交，不使用 PR 合并前的 head。

```bash
set -euo pipefail
RELEASE_REPO=$(git rev-parse --show-toplevel)
RELEASE_VERSION='<VERSION>'
RELEASE_COMMIT='<FULL_MERGED_COMMIT_SHA>'
RELEASE_CI_RUN='<SUCCESSFUL_AGENT_PLUGIN_RUN_ID>'
RELEASE_TAG="nacos-ai-registry-v${RELEASE_VERSION}"
RELEASE_RUN=$(mktemp -d "${TMPDIR:-/tmp}/nacos-agent-release.XXXXXX")
RELEASE_WORKTREE="$RELEASE_RUN/source"
RELEASE_ASSETS="$RELEASE_RUN/assets"
RELEASE_NOTES="$RELEASE_RUN/release-notes.md"
git fetch origin develop --tags
test "$(git rev-parse "${RELEASE_COMMIT}^{commit}")" = "$RELEASE_COMMIT"
git merge-base --is-ancestor "$RELEASE_COMMIT" origin/develop
git worktree add --detach "$RELEASE_WORKTREE" "$RELEASE_COMMIT"
test -z "$(git -C "$RELEASE_WORKTREE" status --porcelain)"
mkdir "$RELEASE_ASSETS"
```

准备好具体产物和说明后再执行推送、上传等远端写入。用户已明确授权发布时，不额外要求重复确认。

## 3. 自动检查与人工验收

构建机需要 Python 3.11+、Node.js 22+、Git 和已登录且具有发布权限的 `gh`。
首次安装依赖需要网络；插件运行不需要 Node.js 或 Maven。各适配使用自己的锁定依赖和独立虚拟环境。

```bash
for host in codex qoder; do
  python3 -m venv "$RELEASE_RUN/venv-$host"
  release_python="$RELEASE_RUN/venv-$host/bin/python"
  "$release_python" -m pip install -r "$RELEASE_WORKTREE/agent-plugins/$host/requirements-build.txt"
  (
    cd "$RELEASE_WORKTREE/agent-plugins/$host"
    PYTHONPATH=src "$release_python" -m unittest discover -s tests -v
    if [ "$host" = codex ]; then node --test tests/test_ui_model.cjs; fi
    "$release_python" scripts/build.py
    "$release_python" scripts/check_package.py
  ) > "$RELEASE_RUN/$host-checks.log" 2>&1
  tail -n 6 "$RELEASE_RUN/$host-checks.log"
done
test -z "$(git -C "$RELEASE_WORKTREE" status --porcelain)"
gh run view "$RELEASE_CI_RUN" --repo nacos-group/nacos-plugin \
  --json conclusion,headSha,event,url,jobs > "$RELEASE_RUN/ci.json"
```

读取日志和 `ci.json`，确认当次测试和所有必需 CI 作业通过。目前为四组 Ubuntu/macOS ×
Python 3.11/3.13 的双端检查，加一组真实 Nacos 集成，共五个 job。数量和环境随 workflow 演进，
说明中填写实际结果，不能仅看 job 数量。

CI 可能运行在 PR head 或合并测试引用，正式包来自合并提交，必须分别记录 SHA。
两者不同时，比较 `agent-plugins/`、对应 workflow 和 `LICENSE`，确认受测内容一致；
本地没有 PR head 时先拉取 `refs/pull/<PR>/head`。有影响发布内容的差异时补齐检查，不能借用旧 CI。
也可在发布提交对应的分支手动触发 workflow，并核对实际 `headSha`。
真实 Nacos 固定源码、鉴权组合和执行方式见[集成测试说明](../integration/README.md)。

人工验收使用当前版本清单；0.1.1 的例子见[本地验收清单](../specs/0.1.1-local-acceptance.md)。
区分通过、失败、受阻、未执行和不适用。CI 不替代页面、钥匙串、原生加载、模型交互和带状态升级/卸载。
待验项及影响保留在发行说明；秘密泄露、数据破坏、未授权写入、主流程失效等已知问题阻止发布。
代码、依赖或打包输入改变后重跑受影响检查；同一份已验证输入不反复运行无关测试。

## 4. 汇集并核对八个附件

| 宿主 | 安装包 | 源码包 | 校验文件 |
| --- | --- | --- | --- |
| Codex | `nacos-ai-registry-<VERSION>.zip` | `nacos-ai-registry-<VERSION>-source.zip` | 每个 ZIP 后追加 `.sha256` |
| Qoder | `nacos-ai-registry-qoder-<VERSION>.zip` | `nacos-ai-registry-qoder-<VERSION>-source.zip` | 每个 ZIP 后追加 `.sha256` |

安装包包含对应宿主的 manifest、Skills、运行程序、许可证及源码，不混入另一宿主的实现。
Codex 源码包保留 `codex/`、共享 `specs/` 及许可证；Qoder 源码包包含 `qoder/`、构建依赖源码、
许可证和 provenance。GitHub 自动生成的 Source code ZIP/tar.gz 不是这两个专用源码包，不计入八个上传附件。

各宿主 `check_package.py` 验证完整格式、文档引用、许可证、隔离启动和源码重建。
联合检查器进一步核对八件套、校验文件中的摘要及文件名、安装包与源码包逐文件对应、源码树摘要，
以及版本、`build-info.json` 中的合并提交和 `dirty: false`。
Codex 当前源码 ZIP 不带 `build-info.json`，通过源码树摘要及安装包内源码验证对应关系。

```bash
for suffix in '' '-source'; do
  for checksum in '' '.sha256'; do
    cp "$RELEASE_WORKTREE/agent-plugins/codex/dist/nacos-ai-registry-${RELEASE_VERSION}${suffix}.zip${checksum}" "$RELEASE_ASSETS/"
    cp "$RELEASE_WORKTREE/agent-plugins/qoder/dist/nacos-ai-registry-qoder-${RELEASE_VERSION}${suffix}.zip${checksum}" "$RELEASE_ASSETS/"
  done
done
python3 "$RELEASE_WORKTREE/agent-plugins/scripts/check_release.py" \
  --version "$RELEASE_VERSION" --commit "$RELEASE_COMMIT" --artifacts-dir "$RELEASE_ASSETS"
```

还需审阅变更和 ZIP 清单，排除客户原图、私有业务资料、真实地址/账号/秘密、状态、日志和演示环境数据。
联合检查器不能证明内容没有秘密，也不能证明 CI 或人工验收通过。个人配置、原始日志和验收环境留在仓库及附件之外。

## 5. 准备英文发行说明

复制[模板](../release-notes/TEMPLATE.md)填写本次版本，或将版本 PR 中的 `release-notes/<VERSION>.md`
整理为实际发布文案，保存到 `$RELEASE_NOTES`。发布后将同一文案同步回仓库版本说明；
事后文档提交不改变已发布 tag 的指向。

1. 使用统一标题，以用户可见变化开头；按需保留 Features、Improvements、Fixes，删除空栏目。
2. Upgrade 写实际兼容影响、状态保留、计划重建及重载要求，不机械照抄旧版。
3. Verification and CI 写真实数量、Nacos 固定源码、环境、测试替身边界和 CI 链接。
4. Compatibility 明确 Python、执行位置、操作系统、认证、页面/协议与加载限制；新增支持须有证据。
5. Pending host acceptance 列出未完成项目及影响，不将未验证写成失败，也不删除待验项营造全通过。
6. Distribution files 固定四个 ZIP 的表格，说明配套 SHA-256，提供安装指南和校验示例。
7. Release verification 写最终 tag、合并提交、干净构建、本地结果与 CI head，分清各自验证对象。
8. 正式文案使用“本版本包含/已构建”，删除“源码更新不会创建 Release”等准备阶段表述。
   Release 页面中的链接必须可访问，优先使用对应 tag 的绝对链接。

实际样例见[0.1.1 发行说明](../release-notes/0.1.1.md)和
[已发布 Release](https://github.com/nacos-group/nacos-plugin/releases/tag/nacos-ai-registry-v0.1.1)。
其中版本、数量、CI run、日期和待验范围属于历史事实，不是后续版本默认值。

## 6. Tag、草稿与远端核对

先检查已有 tag、Release 并记录原 Latest；已有项按第 8 节恢复，不直接重建或覆盖。

```bash
git -C "$RELEASE_REPO" tag --list "$RELEASE_TAG"
git -C "$RELEASE_REPO" ls-remote origin "refs/tags/$RELEASE_TAG" "refs/tags/$RELEASE_TAG^{}"
gh release list --repo nacos-group/nacos-plugin --limit 100
gh api repos/nacos-group/nacos-plugin/releases/latest --jq .tag_name > "$RELEASE_RUN/latest-before.txt"
```

确认 tag 和 Release 均不存在、文案已定稿且用户已授权发布后执行：

```bash
git -C "$RELEASE_REPO" tag -a "$RELEASE_TAG" "$RELEASE_COMMIT" \
  -m "Nacos AI Registry Codex and Qoder ${RELEASE_VERSION}"
test "$(git -C "$RELEASE_REPO" rev-parse "${RELEASE_TAG}^{commit}")" = "$RELEASE_COMMIT"
git -C "$RELEASE_REPO" push origin "refs/tags/$RELEASE_TAG"
release_prerelease=false
case "$RELEASE_VERSION" in *-*) release_prerelease=true;; esac
gh release create "$RELEASE_TAG" \
  "$RELEASE_ASSETS/nacos-ai-registry-${RELEASE_VERSION}.zip" \
  "$RELEASE_ASSETS/nacos-ai-registry-${RELEASE_VERSION}.zip.sha256" \
  "$RELEASE_ASSETS/nacos-ai-registry-${RELEASE_VERSION}-source.zip" \
  "$RELEASE_ASSETS/nacos-ai-registry-${RELEASE_VERSION}-source.zip.sha256" \
  "$RELEASE_ASSETS/nacos-ai-registry-qoder-${RELEASE_VERSION}.zip" \
  "$RELEASE_ASSETS/nacos-ai-registry-qoder-${RELEASE_VERSION}.zip.sha256" \
  "$RELEASE_ASSETS/nacos-ai-registry-qoder-${RELEASE_VERSION}-source.zip" \
  "$RELEASE_ASSETS/nacos-ai-registry-qoder-${RELEASE_VERSION}-source.zip.sha256" \
  --repo nacos-group/nacos-plugin --verify-tag --draft --latest=false \
  --prerelease="$release_prerelease" --title "Nacos AI Registry Agent Plugins ${RELEASE_VERSION}" \
  --notes-file "$RELEASE_NOTES"
```

Tag 不会自动触发当前 Agent plugin workflow 或创建 Release。草稿网址可能带 `untagged-...`，
不能据此认定 tag 失败。按 tag 查询 REST 接口可能取不到草稿，改用有权限的 Release 列表：

```bash
gh api 'repos/nacos-group/nacos-plugin/releases?per_page=100' \
  --jq ".[] | select(.tag_name == \"$RELEASE_TAG\")" > "$RELEASE_RUN/release-draft.json"
python3 "$RELEASE_WORKTREE/agent-plugins/scripts/check_release.py" \
  --version "$RELEASE_VERSION" --commit "$RELEASE_COMMIT" --artifacts-dir "$RELEASE_ASSETS" \
  --release-json "$RELEASE_RUN/release-draft.json" --notes-file "$RELEASE_NOTES" --stage draft
```

必须只匹配一个草稿。核对标题、tag、草稿/预发布标记、完整说明、八个附件的 `uploaded`、大小和
GitHub 返回的 `sha256:` 摘要；回看远端 tag 解析后的提交也与 `$RELEASE_COMMIT` 一致。
若 API 不返回摘要，不跳过核对：下载草稿附件至独立目录，逐字节比较后记录人工验证。
此时检查器仍会失败，不得把它记为通过。

## 7. 发布与收尾

草稿检查完成后发布，再回读公开状态和全部附件：

```bash
gh release edit "$RELEASE_TAG" --repo nacos-group/nacos-plugin --draft=false --latest=false
gh api "repos/nacos-group/nacos-plugin/releases/tags/$RELEASE_TAG" > "$RELEASE_RUN/release-published.json"
python3 "$RELEASE_WORKTREE/agent-plugins/scripts/check_release.py" \
  --version "$RELEASE_VERSION" --commit "$RELEASE_COMMIT" --artifacts-dir "$RELEASE_ASSETS" \
  --release-json "$RELEASE_RUN/release-published.json" --notes-file "$RELEASE_NOTES" --stage published
gh api repos/nacos-group/nacos-plugin/releases/latest --jq .tag_name > "$RELEASE_RUN/latest-after.txt"
diff -u "$RELEASE_RUN/latest-before.txt" "$RELEASE_RUN/latest-after.txt"
```

若 Latest 不同，先检查是否有其他维护者同时发布，不自动改回。保留八个已验证附件、最终说明及
必要验证记录后，移除本次临时工作树：

```bash
# 先完成本地交付文件留存；不使用 --force。
git -C "$RELEASE_REPO" worktree remove "$RELEASE_WORKTREE"
```

同步回本地 `dist/` 时只复制本版本的明确文件并核对摘要，展开目录也须来自同一 ZIP。
不要在有未提交文档的源码中重建同名版本以替代已验证包。交付 Release 链接、本地安装包位置、
版本/提交、验证摘要及待验项，并按项目约定更新工作记录。个人路径和备份不进入公共说明。

## 8. 中断与失败处理

| 情况 | 处理 |
| --- | --- |
| Tag 已存在 | 核对本地/远端解析后的 commit；一致可继续检查 Release，不一致停止，不 force push |
| Tag 已推送但没有 Release | 复核本地八个文件、提交和 tag，继续创建草稿，不打第二个 tag |
| 草稿上传中断 | 读取草稿和附件，核对后只补缺少的文件，再验完整八件套，不盲目重复 create |
| 草稿附件错误 | 核实仍是草稿后移除错误附件、上传正确文件并记录原因；不覆盖已发布附件 |
| 写入超时、结果未知 | 先读取远端 tag/Release/附件状态，再决定是否重试 |
| 已发布内容错误 | 保留原 tag 和附件，说明影响并发布修正版，不静默替换 ZIP 或改写历史 |
| 连接器缺少发布能力 | 在已有授权内使用已登录的 `gh`；权限不足明确报告，不把 draft 当成已发布 |

## 9. 全新安装测试单独执行

常规发布和升级保留 profile、凭据、Skill 和连接。只有用户明确要求从零验收时才清理；
这不是发布脚本的默认步骤，也不影响另一宿主或 Nacos 远端资源。

先构建并验证新包，再进行重置：

1. 确认旧插件准确 ID、安装来源、状态目录和配置归属，区分本地与账户来源。
2. 在仓库外以受限权限备份配置和状态，不把秘密输出到对话或日志。
3. 使用宿主支持的卸载入口；“已禁用”与“已卸载”分别核对。
4. 只移除插件拥有的 MCP 配置和专属安装源，保留共享来源及其他配置。
5. 按原凭据引用和状态目录作用域清除系统凭据并核对；卸载不会自动清理钥匙串。
6. 处理仍运行的旧插件进程，再归档旧状态，避免旧进程写回。
7. 下载的 Skill、本地修改和远端资源按归属单独判断，不直接删除用户技能目录。
8. 核对安装记录、缓存、配置、凭据和活动状态，再用新包、新本地会话验收初始化。

演示 MCP 服务及代码独立保存、启动和验证；卸载插件不表示服务已停止，服务启动不表示已注册到
Nacos。恢复的历史演示源码须说明验证程度，不随正式包发布。
