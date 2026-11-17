# sing-box SFA / SFL builds

English | [Simplified Chinese](README.zh.md)

This repository builds GUI clients for two derivative branch families of [sing-box](https://github.com/SagerNet/sing-box) from upstream public source, entirely in GitHub Actions — no local build environment is required:

- **SFA** — Android GUI (APK)
- **SFL** — Linux GUI (`.deb`)

> **Unofficial project.** This repository only builds installers from the public source of the upstream forks. It is not affiliated with, and does not represent, SagerNet, reF1nd, MiChongs or their maintainers. All source code and artifacts follow their respective upstream licenses; comply with the applicable terms and assess the risk of use yourself.

## Supported variants and source coordinates

| Variant | core | SFA source (Android) | SFL source (Linux) |
| --- | --- | --- | --- |
| xiaobaf14g | `MiChongs/sing-box@xiaobaf14g-testing` | `MiChongs/sing-box-for-android@xiaobaf14g-testing` | `MiChongs/sing-box-for-desktop@xiaobaf14g-dev` |
| reF1nd | `reF1nd/sing-box@reF1nd-testing-next` | `reF1nd/sing-box-for-android@reF1nd-testing` | `reF1nd/sing-box-for-desktop@reF1nd-dev` |

The two variants come from branches maintained by different people and carry independent version numbers (set via `version_xiaobaf14g` / `version_ref1nd` respectively). Within one variant, SFA / SFL use the same version as the corresponding core, keeping versions aligned.

## Build artifacts

Each run produces the following files for the selected variant(s):

- **SFA**: `SFA-<version>-arm64-<variant>.apk` — Android, arm64, standard (`other` flavor)
- **SFL**: `SFL-<version>-x64-<variant>.deb` — Linux, amd64, GPG-signed

With `variant=both` a single run produces both artifact types for both variants (4 files); `variant=xiaobaf14g` / `variant=reF1nd` build only a single variant; `target=sfa` / `target=sfl` build only one artifact type.

## Fixed build tags

Both variants and both artifact types use the following tag set (defined as the workflow's `env.BUILD_TAGS`, without `with_naive_outbound`):

```
with_quic,with_dhcp,with_utls,with_clash_api,with_tailscale,with_xhttp,with_conntrack,badlinkname,tfogo_checklinkname0
```

How it is applied:

- **SFL (`build_boxdd`)**: with cgo disabled (empty `CC`) it reads `release/DEFAULT_BUILD_TAGS_OTHERS`. The workflow overwrites that file (and `release/DEFAULT_BUILD_TAGS`) with the tag set above and keeps `CC` empty and `CGO_ENABLED=0`, so naive is not pulled in and no cronet-go / Chromium toolchain is needed.
- **SFA (`build_libbox`)**: `build_libbox` hardcodes its tags in `sharedTags` in `cmd/internal/build_libbox/main.go` with no CLI switch. The workflow uses [scripts/patch_build_libbox.py](scripts/patch_build_libbox.py) to rewrite it to the tag set above, then builds the arm64 `libbox.aar`.

## About CGO

- **Go toolchain default**: `CGO_ENABLED=1` for native builds, `0` for cross builds.
- **This workflow controls it explicitly**:
  - SFL (linux/amd64): disabled (empty `CC`, `CGO_ENABLED=0`), using `DEFAULT_BUILD_TAGS_OTHERS`; no cronet needed.
  - SFA (android/arm64): enabled (`gomobile bind` and the NDK require cgo).

## About legacy

`build_libbox` originally also produced a legacy (API 21) library `libbox-legacy.aar`. Before building, [scripts/patch_build_libbox.py](scripts/patch_build_libbox.py) removes that legacy branch, so only the arm64 `libbox.aar` is produced, no `libbox-legacy.aar` and no legacy APK.

## How it works (core injection)

- **SFA**: the core is built into a gomobile library `libbox.aar`, placed in the client's `app/libs/`, and the `other` flavor references it via `implementation(files("libs/libbox.aar"))`.
  Build command (inside the core repo): `go run ./cmd/internal/build_libbox -target android -platform android/arm64`.
- **SFL**: `scripts/sing-box.ts`'s `findBoxDirectory()` looks in `<client>/../..` for a directory whose `go.mod` has `module github.com/sagernet/sing-box`; `scripts/package.ts` calls the core's `go run ./cmd/internal/build_boxdd -target=linux/amd64` to build the daemon, then electron-builder packages the `.deb`.
  So the workflow checks out the core at the workspace root and the desktop client at `clients/desktop` (`<client>/../..` is the core root).

## Repository layout

```
.
├── .github/workflows/build-sfa-sfl.yml   # the single workflow
├── scripts/
│   ├── matrix.py                          # builds prepare / sfa / sfl matrices and meta / tag from inputs
│   ├── patch_build_libbox.py              # rewrites build_libbox tags and removes the legacy build
│   ├── restrict_abi.py                    # rewrites the client splits.abi to build arm64-v8a only
│   ├── pin_android_application_id.py      # pins SFA applicationId (same package name across variants)
│   └── pin_desktop_package_name.py        # pins SFL deb package name / appId / executable name
├── .gitignore
├── README.md                              # English (default)
└── README.zh.md                           # Simplified Chinese
```

## Package-name pinning (cross-variant overwrite install)

The two variants (reF1nd / MiChongs) build the **same application**: the SFA `applicationId` and the SFL deb `Package` stay identical between them, so either variant's artifact can be installed over a device/system that already has the other variant (sharing the same app data / config directory).

To ensure upstream code updates cannot rename the package and break this interoperability, the build **forces** the package identity with scripts (idempotent; follows upstream code while pinning the package name):

- **SFA**: [scripts/pin_android_application_id.py](scripts/pin_android_application_id.py) pins the `applicationId` in `app/build.gradle.kts` to `io.reF1nd.sfa`.
- **SFL**: [scripts/pin_desktop_package_name.py](scripts/pin_desktop_package_name.py) pins `package.json`'s `name` (the source of the deb `Package:` field) to `sing-box-for-desktop-ref1nd`, `desktopName` to `sing-box-reF1nd.desktop`, and `electron-builder.yml`'s `appId` / `productName` / `linux.appId` / `linux.executableName`.

Beyond the identical package name, the SFA `versionCode` uses a unified base (`SFA_VERSION_CODE_BASE + github.run_number`, identical for both variants within one run), and a SFL deb with a different version is installed over the existing one via `dpkg` / `apt` (downgrading if necessary). This allows either variant to be installed over the other.

## Usage

On the repository's **Actions** page, pick **Build SFA & SFL** → **Run workflow**, fill in the parameters below and run. Build artifacts are downloadable from that run's Artifacts; when `publish=true` they are also published to the **Releases** page.

### Run parameters

| Parameter | Description |
| --- | --- |
| `variant` | `both` / `xiaobaf14g` / `reF1nd` |
| `target` | `both` / `sfa` / `sfl` (build only one artifact type; default `both`) |
| `version_xiaobaf14g` | xiaobaf14g version (without `v`), e.g. `1.15.0-alpha.13-xiaobaf14g.11`; required when `xiaobaf14g` / `both` is selected |
| `version_ref1nd` | reF1nd version (without `v`); required when `reF1nd` / `both` is selected |
| `prerelease` | Whether to mark the Release as a prerelease |
| `publish` | Whether to create / update a GitHub Release |

The versions of the two variants are set separately via `version_xiaobaf14g` / `version_ref1nd`; with `variant=both` both are required.

### Secrets

Signing material is provided as repository Secrets for CI to sign packages:

| Secret | Description |
| --- | --- |
| `SFA_KEYSTORE_FILE` | base64 (single line) of the Android signing keystore |
| `SFA_KEYSTORE_PASSWORD` | keystore password |
| `SFA_KEY_ALIAS` | key alias |
| `SFA_KEY_PASSWORD` | key password (same as the keystore password for PKCS12) |
| `GPG_KEY` | ASCII-armored private key (with BEGIN/END lines) for signing the SFL `.deb` |
| `GPG_KEY_ID` | signing key fingerprint |
| `GPG_PASSPHRASE` | private key passphrase |

> Signing material must be generated and kept by the maintainer; never write it into repository files or logs.

### Deploy in your own repository (optional)

To reproduce this build in a fork or a standalone repository:

1. Fork this repository, or create a new repository and commit / push this directory's contents.
2. Under **Settings → Secrets and variables → Actions**, configure the Secrets above.
3. Run **Actions → Build SFA & SFL → Run workflow**.

## Workflow structure

- `resolve`: `scripts/matrix.py` produces the `prepare` / `sfa` / `sfl` matrices plus the `meta` / `tag` outputs (each variant and its own version are wrapped in `meta`). The release tag uses everything before the last `-` of the version as its base (e.g. `1.15.0-alpha-reF1nd.11` → `1.15.0-alpha`): `variant=both` uses the bare base (both variants must share the base so they share one Release); `variant=xiaobaf14g` / `variant=reF1nd` append `-xiaobaf14g` / `-reF1nd` after the base.
- `prepare`: per variant, warms the `~/go/pkg/mod` module cache with `go list -deps` (`lookup-only` save, reused by later jobs and later runs; a warm-up failure only warns).
- `sfa-lib`: checks out core + builder scripts → `patch_build_libbox.py` (rewrite tags, drop legacy) → `make lib_install` + `build_libbox` (android/arm64) → uploads `libbox.aar`.
- `sfa`: checks out the client + builder scripts → `restrict_abi.py` (limit `splits.abi` to `arm64-v8a` only) → `pin_android_application_id.py` (pin `applicationId`) → downloads `libbox.aar` into `app/libs` → updates `version.properties` → injects signing → `./gradlew assembleOtherRelease` (no `-Pandroid.injected.build.abi`) → uploads the APK.
- `sfl`: checks out core + client + builder scripts → `pin_desktop_package_name.py` (pin deb package name / appId / executable name) → overwrites `release/DEFAULT_BUILD_TAGS*` → Rust/Zig (wayland native module) → `pnpm package:linux -- deb x64` (empty `CC`, no cronet) → `debsigs` signing → uploads the `.deb`.
- `publish`: aggregates apk / deb, composes the release page (name, versions, build tags, variants, source refs, artifact table) and creates / updates the Release. Single-artifact (`target=sfa`/`sfl`) runs also publish.

## Caching and speed

- **Go modules**: `prepare` warms `~/go/pkg/mod` per variant with `go list -deps` (`lookup-only` save); each build job only `actions/cache/restore`s it.
- **Go build cache**: `~/.cache/go-build`, cached separately for SFA / SFL; the primary key is `go.sum` + tags + variant (**without the commit SHA**, so entries are added only when dependencies change, avoiding growth on every commit); `restore-keys` fall back on the `gobuild-$os-<job>-<variant>-` prefix, so even when `go.sum` changes the most recent cache is hit and builds stay incremental.
- **Gradle**: `gradle/actions/setup-gradle` (`cache-provider: basic`).
- **pnpm / Node**: `actions/setup-node` pnpm store cache + `~/.cache/electron`, `~/.cache/electron-builder`.
- **Rust**: `~/.cargo/registry`, `~/.cargo/git`, `clients/desktop/bin/wayland-menu-toolchain` (keyed on `Cargo.lock`).
- **Zig**: handled by `mlugg/setup-zig`'s own cache (the earlier explicit `~/.cache/zig` cache step was removed because that path does not exist and always missed).
- **Capacity and eviction**: GitHub Actions cache is per-repository with a **10 GiB** cap, evicting by LRU, plus automatic removal after 7 days without access. Current usage is far below the cap.
- All Actions are pinned to commit SHAs; each job sets `timeout-minutes`; `concurrency` cancels older in-flight runs with the same parameters; artifacts are kept for 7 days.

## Resource and runner requirements

- SFA's Gradle build has a high memory peak (the client's `gradle.properties` defaults to `org.gradle.jvmargs=-Xmx8192m`, i.e. an 8 GB heap, on top of the Kotlin compile daemon, R8 and Lint's separate JVMs).
- Building on a `ubuntu-latest` runner with ≥ 4 vCPU / 16 GB is recommended; under constrained resources, lower the Gradle heap (e.g. `-Xmx3g`~`-Xmx4g`), limit `--max-workers`, skip release Lint (`-x lintVitalOtherRelease`), add swap, or use a larger self-hosted runner.
- SFL runs on `ubuntu-26.04`; constrained environments can switch to an available runner label.

## Known limitations

- reF1nd's client repositories have no `reF1nd-testing-next` branch, so the core uses `reF1nd-testing-next`, SFA uses `reF1nd-testing`, and SFL uses `reF1nd-dev`.
- SFA uses [scripts/restrict_abi.py](scripts/restrict_abi.py) to rewrite the client's `app/build.gradle.kts` so that `splits.abi.include(...)` covers only `arm64-v8a` (with `isUniversalApk=false`) before building, so only arm64 is built and artifacts land in `app/build/outputs/apk/other/release/`. It does not use `-Pandroid.injected.build.abi`: that IDE-injection parameter redirects artifacts into `intermediates/` and produces no collectable signed APK.
- [patch_build_libbox.py](scripts/patch_build_libbox.py) relies on the existing structure of `sharedTags` and the legacy build in the `build_libbox` source; if upstream changes break the match, the script warns and continues as-is.
- `build_libbox` requires a `make lib_install` target and Android NDK r28+.
- This build's fixed tag set drops `with_naive_outbound` from the upstream `sharedTags`, and also drops `ts_omit_*`, `with_wireguard` / `with_openvpn` / `with_openconnect` / `with_usbip`, etc.; accordingly artifacts lack these features and tailscale is built with all features (larger size). With the current tag set, both SFA (`libbox.aar`) and SFL have been verified to compile successfully.
- The build source always follows the latest commit of each upstream branch (branch ref, not pinned to a SHA); the `version_*` inputs only affect naming and version metadata and **do not change the code that is fetched/built**. So the same inputs at different times may build different upstream code. For reproducible builds, pin `*_ref` in `scripts/matrix.py` to a specific commit SHA / tag.

## License and credits

This repository itself contains only build-orchestration scripts (the workflow and Python helpers). The sing-box and GUI client sources it builds upon are copyrighted by their respective authors and follow their own open-source licenses; the distributed installers are build artifacts of those sources and must likewise comply with the corresponding licenses.
