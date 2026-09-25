# SoulSign — GitHub 直接上传版

这个仓库版本**不需要在 Windows 本地运行 `bootstrap.sh`**。

## 使用方法

1. 把本 ZIP 解压后的**所有内容**上传/覆盖到你的 GitHub 仓库根目录。
2. 可选：把你设计好的 `soulsign.png` 放到仓库根目录（建议 1024×1024 PNG）。
3. 进入 GitHub 仓库 **Actions → SoulSign Build & Release → Run workflow**。
4. `release_tag` 留空：只生成 Actions Artifact。
5. `release_tag` 填 `v0.1.0` 之类：同时发布到 GitHub Releases。

GitHub Actions 会自动：

- 拉取 `dmjorb/MJorb` 完整源码；
- 应用 SoulSign 修改；
- 检查/构建 RustBridge；
- 应用 `soulsign.png`；
- 生成 Xcode 工程；
- 编译 `SoulSign.ipa`；
- 输出 SHA-256；
- 同时打包生成后的完整源码 `SoulSign-source.zip`。

因此不会再出现“因为你 Windows 没有 bash，所以无法生成完整仓库”的问题。

## 注意

如果 Actions 在第一步 `git clone https://github.com/dmjorb/MJorb.git` 报错，说明上游仓库地址、访问权限或分支发生变化；这和 Windows Git/bash 无关。

## v3 bootstrap fix

The bootstrap now copies the workflow from `.github/workflows/soulsign-build.yml`
instead of the removed/nonexistent `overlay/.github/...` path.


## v4 patch robustness

- Fixes MJorb `project.yml` having more than one `CFBundleDisplayName: Seal`.
- SoulSign now patches only the main `targets -> Seal` block for app display name, URL scheme and BGTask Info.plist keys.
- Generic source replacements tolerate duplicate matches by patching the first exact match and logging a warning.
- Bootstrap prints the exact MJorb upstream commit SHA in Actions logs.

## v5 build stability

The default MJorb source is pinned to commit `4c24fda2c97f8d275b748ba069a9af0ba89b62d2`. This makes builds reproducible instead of silently following upstream `main`. The direct-sign capacity guard now patches by function entry and degrades to a warning if upstream renames that helper; the primary 3-app account-pool allocator remains active.
