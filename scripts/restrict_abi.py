#!/usr/bin/env python3
"""把 Android 客户端限制为只构建 arm64-v8a。

改写目标文件 app/build.gradle.kts 中的 splits.abi 块：
  - include("armeabi-v7a", "arm64-v8a", "x86", "x86_64")  ->  include("arm64-v8a")
  - isUniversalApk = true  ->  isUniversalApk = false（避免多余的 universal APK）

只影响 ABI 打包，不改变签名/版本/其它逻辑；不含 `-Pandroid.injected.build.abi`
（IDE 注入式构建会把产物导向 intermediates，故不使用）。

用法: python3 restrict_abi.py <path/to/app/build.gradle.kts>
幂等：当已是仅 arm64-v8a 时直接成功返回。
"""

import re
import sys

# 匹配 splits { abi { ... include("...") ... } } 中的 include(...)
_RE_SPLITS = re.compile(
    r"(splits\s*\{\s*abi\s*\{[^{}]*?include\()([^)]*)(\))", re.S
)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: restrict_abi.py <app/build.gradle.kts>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
    except OSError as e:
        print(f"::error::cannot read {path}: {e}", file=sys.stderr)
        return 1

    m = _RE_SPLITS.search(src)
    if not m:
        print(f"::error::splits.abi.include not found in {path}", file=sys.stderr)
        return 1

    current = [a.strip().strip('"') for a in m.group(2).split(",") if a.strip()]
    if current == ["arm64-v8a"]:
        print(f"already arm64-v8a only: {path}")
        return 0

    out = _RE_SPLITS.sub(r'\1"arm64-v8a"\3', src, count=1)
    out = out.replace("isUniversalApk = true", "isUniversalApk = false")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"patched splits.abi {current} -> ['arm64-v8a'] in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
