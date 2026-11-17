#!/usr/bin/env python3
"""Pin the Android applicationId to a fixed value.

Rewrites the `applicationId = "..."` line in app/build.gradle.kts (defaultConfig)
to a fixed id, so the SFA built from any variant always shares the same
package identity and can be installed over the other variant.

Usage: python3 pin_android_application_id.py <app/build.gradle.kts> [applicationId]
Idempotent: exits 0 if it already equals the target.
"""

import re
import sys

DEFAULT_ID = "io.reF1nd.sfa"

# applicationId = "io.reF1nd.sfa"  (allow surrounding spaces)
_RE_APPID = re.compile(r'^([ \t]*)applicationId[ \t]*=[ \t]*"([^"]*)"[ \t]*$', re.M)


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: pin_android_application_id.py <app/build.gradle.kts> [applicationId]",
              file=sys.stderr)
        return 2
    path = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_ID

    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
    except OSError as e:
        print(f"::error::cannot read {path}: {e}", file=sys.stderr)
        return 1

    m = _RE_APPID.search(src)
    if not m:
        print(f"::error::applicationId not found in {path}", file=sys.stderr)
        return 1

    current = m.group(2)
    if current == target:
        print(f"already pinned: applicationId = \"{target}\" ({path})")
        return 0

    out = _RE_APPID.sub(lambda mm: f'{mm.group(1)}applicationId = "{target}"', src, count=1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f'pinned applicationId "{current}" -> "{target}" ({path})')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
