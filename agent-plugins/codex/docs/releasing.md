# 发布 Codex 插件

这里的发布是将版本包分发到本仓库的 GitHub Releases；Codex 官方插件目录上架是单独流程，
发布 ZIP 不会自动完成目录上架。当前源码版本为 `0.1.0`，使用不带预发布后缀的版本号。发布前核对
[TODO](../specs/TODO.md)与[兼容范围](compatibility.md)，在发行说明中如实列出已知限制和未完成验证；
更改源码版本号不会自动创建 tag、上传附件或发布 Release。

维护者按以下顺序发布：

1. 同步修改 `plugin.json` 的 `version` 与 `src/nacos_registry/__init__.py` 的 `__version__`，
   更新 README 的版本与验收范围；两处版本不一致时构建会失败。
2. 将改动提交、合并，检出准备发布的提交。确认 `git status --porcelain` 没有输出，
   再完整执行[开发指南](development.md)中的测试、构建和包检查。不要使用此前留在 `dist/` 中的旧包。
3. 检查 `dist/nacos-ai-registry/build-info.json`：版本应正确，`gitBase` 应为准备发布的提交，
   `dirty` 应为 `false`。源码包与安装包必须来自这一次构建。
4. 在仓库外准备发行说明，写明变化、支持环境、安装入口和未完成的验收项，然后创建组件 tag
   和 Release 草稿。下面命令仍在 `agent-plugins/codex/` 中执行，需要 GitHub 推送及发布权限、
   已登录的 `gh`；将发行说明路径替换为实际文件路径。

```sh
PLUGIN_VERSION=$(.venv/bin/python -c 'import json; print(json.load(open("plugin.json"))["version"])')
PLUGIN_TAG="nacos-ai-registry-v${PLUGIN_VERSION}"

git tag -a "$PLUGIN_TAG" -m "Nacos AI Registry ${PLUGIN_VERSION}"
git push origin "refs/tags/${PLUGIN_TAG}"

gh release create "$PLUGIN_TAG" \
  "dist/nacos-ai-registry-${PLUGIN_VERSION}.zip" \
  "dist/nacos-ai-registry-${PLUGIN_VERSION}.zip.sha256" \
  "dist/nacos-ai-registry-${PLUGIN_VERSION}-source.zip" \
  "dist/nacos-ai-registry-${PLUGIN_VERSION}-source.zip.sha256" \
  --repo nacos-group/nacos-plugin \
  --verify-tag --draft --latest=false \
  --title "Nacos AI Registry ${PLUGIN_VERSION}" \
  --notes-file /absolute/path/to/release-notes.md
```

每一步成功后再继续；若 tag 已存在，应先核对它指向的提交，不覆盖已发布版本。
在 GitHub 中核对草稿的 tag、四个附件和发行说明后再发布。`0.1.0` 不勾选 Pre-release；
`dev`、`rc` 等候选版本则添加 `--prerelease`。是否设为仓库最新版本需单独选择，避免覆盖服务端插件的 Release 展示。
下载者应同时获得安装 ZIP 与对应 SHA-256；例如在下载目录使用 macOS 的
`shasum -a 256 -c <安装包文件名>.sha256`，或 Linux 的 `sha256sum -c <安装包文件名>.sha256`。

现有 `.github/workflows/agent-plugin.yml` 会在相关 PR 或手动触发时执行测试和打包，
并保存 ZIP 与校验和为 Actions artifacts。它不会因推送 tag 自动创建或发布 Release；
上述发布步骤需由维护者执行。
