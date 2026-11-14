# TODO / 优化待办

> 记录本构建仓库的后续优化项。当前仅记录，不实施，按优先级逐步推进。

## 待办

- [ ] **构建加入 cache 优化，加快编译**（见下方“cache 优化可落点”清单）

## cache 优化可落点（清单，后续细化）

### Go（SFA 的 libbox / SFL 的 daemon）
- [ ] 缓存 `~/go/pkg/mod`：key 绑定 `go.sum` + `release/DEFAULT_BUILD_TAGS*`
- [ ] 缓存 `~/.cache/go-build`：key 带 `GOOS/GOARCH/tags/commit`，用 `restore-keys` 前缀回退到上一版
- [ ] 参考上游 `xiaobaf14g-release.yml` 的 `prepare` job：用 `go list -deps` 按各目标 tag 组合预热模块缓存，其余 job 只 restore

### Gradle / Android（SFA）
- [ ] `gradle/actions/setup-gradle` 已用 `cache-provider: basic`，可评估 remote build cache
- [ ] `~/.gradle/caches`、`~/.android` 评估缓存
- [ ] NDK：**不要**用 `actions/cache`（clang wrapper 软链会被固化绝对路径），维持 runner 预装 r28+ 或按需下载

### pnpm / Node（SFL）
- [ ] `actions/setup-node` 的 pnpm store 缓存（已启用，依赖 `pnpm-lock.yaml`）
- [ ] dashboard 子模块 `pnpm-lock.yaml` 的缓存路径（已配置）
- [ ] `~/.cache/electron`、`~/.cache/electron-builder` 缓存（electron/打包工具下载大头）

### Rust / Zig（SFL 原生模块）
- [ ] `~/.cargo/registry`、`~/.cargo/git`、native `target/` 按 `Cargo.lock` 缓存（wayland-menu / dashboard 原生模块）
- [ ] Zig 缓存（`mlugg/setup-zig` 自带）

### 跨 job / 跨变体
- [ ] 统一 `prepare` 预热、其余 job 只 restore，避免重复下载
- [ ] 两变体并行时共享同一缓存前缀，`restore-keys` 回退
- [ ] `concurrency` 取消策略 / `artifact retention-days` 调优
- [ ] 评估 self-hosted 或更大 runner 以缩短耗时

## 其他可选优化
- [ ] 将 Actions 钉到 commit SHA（可复现性）
- [ ] 每个 job 增加 `timeout-minutes` 防挂起
- [ ] 评估把 SFA 的 libbox 构建与 gradle 拆成两个 job（当前合并）以更好复用缓存
- [ ] 评估把仓库设为 public 以获不限量 Actions 额度（仓库内无密钥）

## 已知风险（待首跑实测确认）
- [ ] 固定标签集去掉了 `ts_omit_*` / `with_wireguard` 等；若 Android `libbox.aar` 因此编译失败，在 `env.BUILD_TAGS` 末尾补回 `ts_omit_*`
