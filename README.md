# sing-box SFA / SFL 构建

本仓库通过 GitHub Actions，从上游公开源码构建 [sing-box](https://github.com/SagerNet/sing-box) 两个衍生分支体系的 GUI 客户端，全程在 CI 中完成，无需本地编译环境：

- **SFA** — Android GUI（APK）
- **SFL** — Linux GUI（`.deb`）

> **非官方项目。** 本仓库仅从各上游 fork 的公开源码构建安装包，与 SagerNet、reF1nd、MiChongs 及其维护者均无从属关系，亦不代表其立场。所有源码与产物均遵循各自上游许可证，请遵守对应许可条款并自行评估使用风险。

## 支持的变体与源码坐标

| 变体 | core | SFA 源（Android） | SFL 源（Linux） |
| --- | --- | --- | --- |
| xiaobaf14g | `MiChongs/sing-box@xiaobaf14g-testing` | `MiChongs/sing-box-for-android@xiaobaf14g-testing` | `MiChongs/sing-box-for-desktop@xiaobaf14g-dev` |
| reF1nd | `reF1nd/sing-box@reF1nd-testing-next` | `reF1nd/sing-box-for-android@reF1nd-testing` | `reF1nd/sing-box-for-desktop@reF1nd-dev` |

两个变体分别源自不同维护者的分支，版本号各自独立（由 `version_xiaobaf14g` / `version_ref1nd` 分别指定）；同一变体下，SFA / SFL 与对应 core 使用同一版本号，保证版本对齐。

## 构建产物

每次运行按所选变体产出以下文件：

- **SFA**：`SFA-<version>-arm64-<variant>.apk` — Android，arm64，标准版（`other` flavor）
- **SFL**：`<variant>-SFL-<version>-x64.deb` — Linux，amd64，GPG 签名

`variant=both` 时一次产出上述两类 × 两个变体（共 4 个文件）；`variant=xiaobaf14g` / `variant=reF1nd` 只构建单个变体；`target=sfa` / `target=sfl` 可只构建其中一类产物。

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

## 工作原理（core 注入）

- **SFA**：core 编成 gomobile 库 `libbox.aar`，放入客户端 `app/libs/`，`other` flavor 通过 `implementation(files("libs/libbox.aar"))` 引用。
  生成命令（在 core 仓库内）：`go run ./cmd/internal/build_libbox -target android -platform android/arm64`。
- **SFL**：`scripts/sing-box.ts` 的 `findBoxDirectory()` 在 `<client>/../..` 查找 `go.mod` 为 `module github.com/sagernet/sing-box` 的目录；`scripts/package.ts` 调 core 的 `go run ./cmd/internal/build_boxdd -target=linux/amd64` 编守护进程，再由 electron-builder 打成 `.deb`。
  因此工作流将 core 检出到工作区根，桌面客户端检出到 `clients/desktop`（`<client>/../..` 即 core 根）。

## 仓库结构

```
.
├── .github/workflows/build-sfa-sfl.yml   # 唯一工作流
├── scripts/
│   ├── matrix.py                          # 由输入生成 prepare / sfa / sfl 矩阵与 meta / tag
│   ├── patch_build_libbox.py              # 重写 build_libbox 的标签并移除 legacy 构建
│   ├── restrict_abi.py                    # 改写客户端 splits.abi，仅构建 arm64-v8a
│   ├── pin_android_application_id.py      # 固定 SFA 的 applicationId（跨变体同包名）
│   └── pin_desktop_package_name.py        # 固定 SFL 的 deb 包名 / appId / 可执行名
├── .gitignore
└── README.md
```

## 包名固定（跨变体互相覆盖安装）

两个变体（reF1nd / MiChongs）构建的是**同一个应用**：SFA 的 `applicationId`、SFL 的 deb `Package` 在两者间保持固定一致，因此任一变体的产物都可覆盖安装到已装另一变体的设备/系统上（共用应用数据/配置目录）。

为保证上游代码更新不会改名、破坏这种互通，构建时用脚本把包身份**强制固定**（幂等，跟随上游代码但包名固定）：

- **SFA**：[scripts/pin_android_application_id.py](scripts/pin_android_application_id.py) 把 `app/build.gradle.kts` 的 `applicationId` 固定为 `io.reF1nd.sfa`。
- **SFL**：[scripts/pin_desktop_package_name.py](scripts/pin_desktop_package_name.py) 把 `package.json` 的 `name`（deb `Package:` 的来源）固定为 `sing-box-for-desktop-ref1nd`、`desktopName` 固定为 `sing-box-reF1nd.desktop`，并把 `electron-builder.yml` 的 `appId` / `productName` / `linux.appId` / `linux.executableName` 固定。

除包名一致外，SFA 的 `versionCode` 使用统一基准（`SFA_VERSION_CODE_BASE + github.run_number`，同一次运行内两变体相同），SFL 的 deb 在版本不同时由 `dpkg` / `apt` 以覆盖（必要时降级）方式安装。据此可在两个变体间互相覆盖安装。

## 使用方法

在仓库的 **Actions** 页面选择 **Build SFA & SFL** → **Run workflow**，按下方参数填写后运行。构建产物在该次运行的 Artifacts 中下载；当 `publish=true` 时，产物同时发布到 **Releases** 页面。

### 运行参数

| 参数 | 说明 |
| --- | --- |
| `variant` | `both` / `xiaobaf14g` / `reF1nd` |
| `target` | `both` / `sfa` / `sfl`（仅构建其中一类产物；默认 `both`） |
| `version_xiaobaf14g` | xiaobaf14g 版本号（不含 `v`），如 `1.15.0-alpha.13-xiaobaf14g.11`；选 `xiaobaf14g` / `both` 时必填 |
| `version_ref1nd` | reF1nd 版本号（不含 `v`）；选 `reF1nd` / `both` 时必填 |
| `prerelease` | 是否将 Release 标记为 prerelease |
| `publish` | 是否创建 / 更新 GitHub Release |

两个变体的版本号分别由 `version_xiaobaf14g` / `version_ref1nd` 指定；`variant=both` 时两者均需填写。

### Secrets

签名相关材料以仓库 Secrets 形式提供，供 CI 打包时签名使用：

| Secret | 说明 |
| --- | --- |
| `SFA_KEYSTORE_FILE` | 安卓签名 keystore 的 base64（单行） |
| `SFA_KEYSTORE_PASSWORD` | keystore 口令 |
| `SFA_KEY_ALIAS` | 密钥别名 |
| `SFA_KEY_PASSWORD` | 密钥口令（PKCS12 与 keystore 口令一致） |
| `GPG_KEY` | SFL `.deb` 签名用 ASCII-armored 私钥（含 BEGIN/END 行） |
| `GPG_KEY_ID` | 签名密钥指纹 |
| `GPG_PASSPHRASE` | 私钥口令 |

> 签名材料应由维护者自行生成并妥善保管，切勿写入仓库文件或日志。

### 在自有仓库部署（可选）

如需在 fork 或独立仓库中复现本构建：

1. Fork 本仓库，或新建仓库并将本目录内容提交、推送。
2. 在仓库 **Settings → Secrets and variables → Actions** 中配置上述 Secrets。
3. 运行 **Actions → Build SFA & SFL → Run workflow**。

## 工作流结构

- `resolve`：`scripts/matrix.py` 生成 `prepare` / `sfa` / `sfl` 矩阵，以及 `meta` / `tag` 输出（每个变体及其独立版本号封装在 `meta` 中）。发布 tag 以 version 中最后一个 `-` 之前的全部字段为基名（如 `1.15.0-alpha-reF1nd.11` → `1.15.0-alpha`）：`variant=both` 直接用基名（两变体须同基名以共用同一个 Release）；`variant=xiaobaf14g` / `variant=reF1nd` 在基名后再追加 `-xiaobaf14g` / `-reF1nd`。
- `prepare`：按变体用 `go list -deps` 预热 `~/go/pkg/mod` 模块缓存（`lookup-only` 保存，供后续 job 与后续运行复用；预热步骤失败仅告警）。
- `sfa-lib`：检出 core + 构建脚本 → `patch_build_libbox.py`（改标签、去 legacy）→ `make lib_install` + `build_libbox`（android/arm64）→ 上传 `libbox.aar`。
- `sfa`：检出客户端 + 构建脚本 → `restrict_abi.py`（把 `splits.abi` 限定为仅 `arm64-v8a`）→ `pin_android_application_id.py`（固定 `applicationId`）→ 下载 `libbox.aar` 放入 `app/libs` → 更新 `version.properties` → 注入签名 → `./gradlew assembleOtherRelease`（不再传 `-Pandroid.injected.build.abi`）→ 上传 APK。
- `sfl`：检出 core + 客户端 + 构建脚本 → `pin_desktop_package_name.py`（固定 deb 包名 / appId / 可执行名）→ 覆盖 `release/DEFAULT_BUILD_TAGS*` → Rust/Zig（wayland 原生模块）→ `pnpm package:linux -- deb x64`（`CC` 空、无 cronet）→ `debsigs` 签名 → 上传 `.deb`。
- `publish`：汇总 apk / deb，生成发布页（名称、版本、构建标签、变体、来源 refs、产物表）并创建 / 更新 Release。单产物（`target=sfa`/`sfl`）运行也会发布。

## 缓存与加速

- **Go 模块**：`prepare` 按变体用 `go list -deps` 预热 `~/go/pkg/mod`（`lookup-only` 保存），各构建 job 只 `actions/cache/restore` 复用。
- **Go 编译缓存**：`~/.cache/go-build`，SFA / SFL 各自 `actions/cache`；主 key 按 `go.sum` + tags + variant（**不含提交 SHA**，只在依赖变化时才新增条目，避免随每次提交膨胀）；`restore-keys` 以 `gobuild-$os-<job>-<variant>-` 前缀回退，因此即便 `go.sum` 变化也能命中最近一次缓存、保持增量编译。
- **Gradle**：`gradle/actions/setup-gradle`（`cache-provider: basic`）。
- **pnpm / Node**：`actions/setup-node` 的 pnpm store 缓存 + `~/.cache/electron`、`~/.cache/electron-builder`。
- **Rust**：`~/.cargo/registry`、`~/.cargo/git`、`clients/desktop/bin/wayland-menu-toolchain`（按 `Cargo.lock`）。
- **Zig**：由 `mlugg/setup-zig` 自带缓存负责（早期基于 `~/.cache/zig` 的显式缓存步骤因该路径不存在恒 miss，已删除）。
- **容量与淘汰**：GitHub Actions 缓存按仓库计，上限 **10 GiB**，超出按 LRU 淘汰；另有「7 天未访问自动清除」。当前占用远低于上限。
- 所有 Actions 均钉到 commit SHA；各 job 设 `timeout-minutes`；`concurrency` 取消同参数并发旧运行；artifact 保留 7 天。

## 资源与运行器要求

- SFA 的 Gradle 构建内存峰值较高（客户端 `gradle.properties` 默认 `org.gradle.jvmargs=-Xmx8192m`，即 8 GB 堆，叠加 Kotlin 编译守护进程、R8 与 Lint 的独立 JVM）。
- 建议在 ≥ 4 vCPU / 16 GB 的 `ubuntu-latest` 运行器上构建；资源受限时可调低 Gradle 堆（如 `-Xmx3g`~`-Xmx4g`）、限制 `--max-workers`、跳过 release Lint（`-x lintVitalOtherRelease`）、增加 swap，或改用更大的自托管运行器。
- SFL 运行于 `ubuntu-26.04`；受限环境可改用可用的 runner 标签。

## 已知限制

- reF1nd 的客户端仓库无 `reF1nd-testing-next` 分支，故 core 使用 `reF1nd-testing-next`，SFA 使用 `reF1nd-testing`，SFL 使用 `reF1nd-dev`。
- SFA 通过 [scripts/restrict_abi.py](scripts/restrict_abi.py) 在构建前改写客户端 `app/build.gradle.kts` 的 `splits.abi.include(...)` 为仅 `arm64-v8a`（同时 `isUniversalApk=false`），从而只编 arm64、产物落在 `app/build/outputs/apk/other/release/`。不使用 `-Pandroid.injected.build.abi`：该 IDE 注入式参数会把产物导向 `intermediates/`，不产生可收集的签名 APK。
- [patch_build_libbox.py](scripts/patch_build_libbox.py) 依赖 `build_libbox` 源码中 `sharedTags` 与 legacy 构建的既有结构；若上游改写导致不匹配，脚本会打印告警并按现状继续。
- `build_libbox` 需 `make lib_install` 目标与 Android NDK r28+。
- 本构建固定标签集去掉了上游 `sharedTags` 中的 `with_naive_outbound`，同时也去掉了 `ts_omit_*`、`with_wireguard` / `with_openvpn` / `with_openconnect` / `with_usbip` 等；因此产物不含这些特性，且 tailscale 以全特性编译（体积增大）。当前标签集下 SFA（`libbox.aar`）与 SFL 均已实测可成功编译。
- 构建源码始终跟随各上游分支的最新提交（branch ref，不做 SHA 钉定）；`version_*` 输入仅用于命名与版本元数据，**不改变拉取/编译的代码**。因此相同输入在不同时间构建可能对应不同上游代码。若需可复现构建，可将 `scripts/matrix.py` 中的 `*_ref` 固定为具体 commit SHA / tag。

## 许可证与致谢

本仓库自身仅包含构建编排脚本（workflow 与 Python 辅助脚本）。构建所依赖的 sing-box 及各 GUI 客户端源码版权归其各自作者所有，遵循各自仓库的开源许可证；分发的安装包为上述源码的构建产物，请一并遵守相应许可证。
