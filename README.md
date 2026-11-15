# sing-box SFA / SFL 构建仓库

通过 GitHub Actions 从源码构建 sing-box 两个分支体系的图形客户端：

- **SFA**：Android GUI
- **SFL**：Linux GUI

## 变体与源码坐标

| 变体 | core | SFA 源（Android） | SFL 源（Linux） |
| --- | --- | --- | --- |
| xiaobaf14g | `MiChongs/sing-box@xiaobaf14g-testing` | `MiChongs/sing-box-for-android@xiaobaf14g-testing` | `MiChongs/sing-box-for-desktop@xiaobaf14g-dev` |
| reF1nd | `reF1nd/sing-box@reF1nd-testing-next` | `reF1nd/sing-box-for-android@reF1nd-testing` | `reF1nd/sing-box-for-desktop@reF1nd-dev` |

## 构建产物

每次运行按所选变体产出以下两类文件（此外不产出任何附加文件）：

- **SFA**：`SFA-<version>-arm64-<variant>.apk` — Android，arm64，标准版（`other` flavor）
- **SFL**：`<variant>-SFL-<version>-x64.deb` — Linux，amd64，GPG 签名

`variant=both` 时一次产出上述两类 × 两个变体（共 4 个文件）；如需单变体产物，使用 `variant=xiaobaf14g` 或 `variant=reF1nd`；`target=sfa` / `target=sfl` 可只构建其中一类产物。

## 固定构建标签

两个变体、两类产物统一使用以下标签集（定义于 workflow 的 `env.BUILD_TAGS`，不含 `with_naive_outbound`）：

```
with_quic,with_dhcp,with_utls,with_clash_api,with_tailscale,with_xhttp,badlinkname,tfogo_checklinkname0
```

应用方式：

- **SFL（`build_boxdd`）**：cgo 关闭（`CC` 为空）时读取 `release/DEFAULT_BUILD_TAGS_OTHERS`。工作流将该文件（及 `release/DEFAULT_BUILD_TAGS`）覆盖为上述标签集，并保持 `CC` 为空、`CGO_ENABLED=0`，因此不引入 naive，也无需 cronet-go / Chromium 工具链。
- **SFA（`build_libbox`）**：`build_libbox` 的标签写死在 `cmd/internal/build_libbox/main.go` 的 `sharedTags` 且无命令行开关。工作流用 [scripts/patch_build_libbox.py](scripts/patch_build_libbox.py) 将其重写为上述标签集，再编 arm64 的 `libbox.aar`。

## 关于 CGO

- **Go 工具链默认**：本机原生编译时 `CGO_ENABLED=1`；交叉编译时默认为 `0`。
- **本工作流显式控制**：
  - SFL（linux/amd64）：关闭（`CC` 为空、`CGO_ENABLED=0`），使用 `DEFAULT_BUILD_TAGS_OTHERS`，无需 cronet。
  - SFA（android/arm64）：开启（`gomobile bind` 与 NDK 依赖 cgo）。

## 关于 legacy

`build_libbox` 原会同时生成 legacy（API 21）库 `libbox-legacy.aar`。构建前由 [scripts/patch_build_libbox.py](scripts/patch_build_libbox.py) 移除该 legacy 分支构建，因此仅生成 arm64 的 `libbox.aar`，不生成 `libbox-legacy.aar`，也不产出 legacy APK。

## 仓库结构

```
.
├── .github/workflows/build-sfa-sfl.yml   # 唯一工作流
├── scripts/
│   ├── matrix.py                          # 由输入生成 prepare / sfa / sfl 矩阵与 version / meta / tag
│   └── patch_build_libbox.py              # 重写 build_libbox 的标签并移除 legacy 构建
├── .gitignore
└── README.md
```

## 工作原理（core 注入）

- **SFA**：core 编成 gomobile 库 `libbox.aar`，放入客户端 `app/libs/`，`other` flavor 通过 `implementation(files("libs/libbox.aar"))` 引用。
  生成命令（在 core 仓库内）：`go run ./cmd/internal/build_libbox -target android -platform android/arm64`。
- **SFL**：`scripts/sing-box.ts` 的 `findBoxDirectory()` 在 `<client>/../..` 查找 `go.mod` 为 `module github.com/sagernet/sing-box` 的目录；`scripts/package.ts` 调 core 的 `go run ./cmd/internal/build_boxdd -target=linux/amd64` 编守护进程，再由 electron-builder 打成 `.deb`。
  因此工作流将 core 检出到工作区根，桌面客户端检出到 `clients/desktop`（`<client>/../..` 即 core 根）。

## 使用步骤

1. 新建空仓库，将本目录提交并推送。
2. 在仓库 Settings → Secrets and variables → Actions 配置下方 Secrets。
3. 运行 Actions → **Build SFA & SFL** → Run workflow。

### 运行参数

| 参数 | 说明 |
| --- | --- |
| `variant` | `both` / `xiaobaf14g` / `reF1nd` |
| `target` | `both` / `sfa` / `sfl`（仅构建其中一类产物；默认 `both`） |
| `version` | 版本号（不含 `v` 前缀），如 `1.15.0-alpha.13-xiaobaf14g.11` |
| `prerelease` | 是否标记 Release 为 prerelease |
| `publish` | 是否创建 / 更新 GitHub Release |

### Secrets

| Secret | 说明 |
| --- | --- |
| `SFA_KEYSTORE_FILE` | 安卓签名 keystore 的 base64（单行） |
| `SFA_KEYSTORE_PASSWORD` | keystore 口令 |
| `SFA_KEY_ALIAS` | 密钥别名 |
| `SFA_KEY_PASSWORD` | 密钥口令（PKCS12 与 keystore 口令一致） |
| `GPG_KEY` | SFL `.deb` 签名用 ASCII-armored 私钥（含 BEGIN/END 行） |
| `GPG_KEY_ID` | 签名密钥指纹 |
| `GPG_PASSPHRASE` | 私钥口令 |

签名材料在本地生成并保存，勿纳入版本库。

## 工作流结构

- `resolve`：`scripts/matrix.py` 生成 `prepare` / `sfa` / `sfl` 矩阵，以及 `version` / `meta` / `tag` 输出。
- `prepare`：按变体用 `go list -deps` 预热 `~/go/pkg/mod` 模块缓存（`lookup-only` 保存，供后续 job 与后续运行复用；预热步骤失败仅告警）。
- `sfa-lib`：检出 core + 构建脚本 → `patch_build_libbox.py`（改标签、去 legacy）→ `make lib_install` + `build_libbox`（android/arm64）→ 上传 `libbox.aar`。
- `sfa`：检出客户端 → 下载 `libbox.aar` 放入 `app/libs` → 更新 `version.properties` → 注入签名 → `./gradlew assembleOtherRelease -Pandroid.injected.build.abi=arm64-v8a` → 上传 APK。
- `sfl`：检出 core + 客户端 → 覆盖 `release/DEFAULT_BUILD_TAGS*` → Rust/Zig（wayland 原生模块）→ `pnpm package:linux -- deb x64`（`CC` 空、无 cronet）→ `debsigs` 签名 → 上传 `.deb`。
- `publish`：汇总 apk / deb，生成发布页（名称、版本、构建标签、变体、来源 refs、产物表）并创建 / 更新 Release。单产物（`target=sfa`/`sfl`）运行也会发布。

## 缓存与加速

- **Go**：`prepare` 预热 `~/go/pkg/mod`，各构建 job `actions/cache/restore` 复用；`~/.cache/go-build` 按 `go.sum` + variant + SHA 缓存并 `restore-keys` 回退。
- **Gradle**：`gradle/actions/setup-gradle`（`cache-provider: basic`）。
- **pnpm / Node**：`actions/setup-node` 的 pnpm store 缓存 + `~/.cache/electron`、`~/.cache/electron-builder`。
- **Rust / Zig**：`~/.cargo/registry`、`~/.cargo/git`、`clients/desktop/bin/wayland-menu-toolchain`、`~/.cache/zig`。
- 所有 Actions 均钉到 commit SHA；各 job 设 `timeout-minutes`；`concurrency` 取消同参数的并发旧运行。

## 已知限制

- reF1nd 的客户端仓库无 `reF1nd-testing-next` 分支，故 core 使用 `reF1nd-testing-next`、SFA 使用 `reF1nd-testing`、SFL 使用 `reF1nd-dev`。
- SFA 通过 `-Pandroid.injected.build.abi=arm64-v8a` 限定 ABI；若 AGP 未识别该属性，上传的 universal APK 的 JNI 仍仅含 arm64。
- SFL 运行于 `ubuntu-26.04`；受限环境应改用可用的 runner 标签。
- [patch_build_libbox.py](scripts/patch_build_libbox.py) 依赖 `build_libbox` 源码中 `sharedTags` 与 legacy 构建的既有结构；若上游改写导致不匹配，脚本会打印告警并按现状继续。
- `build_libbox` 需 `make lib_install` 目标与 Android NDK r28+。
- 固定标签集按需求去掉了上游 `sharedTags` 中的 `with_naive_outbound`，同时也去掉了 `ts_omit_*`、`with_wireguard`/`with_openvpn`/`with_openconnect`/`with_usbip` 等；因此产物不含这些特性，且 tailscale 以全特性编译（体积增大）。若 Android 端 `libbox.aar` 因缺少 `ts_omit_*` 相关依赖而编译失败，可在 `env.BUILD_TAGS` 末尾补回 `ts_omit_logtail,ts_omit_ssh,ts_omit_drive,ts_omit_taildrop,ts_omit_webclient,ts_omit_doctor,ts_omit_capture,ts_omit_kube,ts_omit_aws,ts_omit_synology,ts_omit_bird`。
