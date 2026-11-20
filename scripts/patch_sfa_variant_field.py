#!/usr/bin/env python3
"""Inject a build-time variant constant into the SFA client.

Adds ``buildConfigField("String", "SFA_VARIANT", "<variant>")`` to the Android
``defaultConfig`` block so the in-app updater can tell which variant it is at
runtime (independent of how the version string is formatted).
"""

import re
import sys
from pathlib import Path

MARKER = '"SFA_VARIANT"'


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: patch_sfa_variant_field.py <app/build.gradle.kts> <variant>")

    path = Path(sys.argv[1])
    variant = sys.argv[2]
    if not path.is_file():
        sys.exit(f"ERROR: file not found: {path}")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", variant):
        sys.exit(f"ERROR: unexpected variant value: {variant!r}")

    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"{path}: SFA_VARIANT buildConfigField already present")
        return

    old = "    defaultConfig {\n"
    if text.count(old) != 1:
        sys.exit(
            f"ERROR: could not locate a single 'defaultConfig {{' block in {path} "
            "(upstream source changed?)"
        )

    kotlin_value = '"\\"' + variant + '\\""'  # -> "\"<variant>\""
    line = '        buildConfigField("String", "SFA_VARIANT", %s)\n' % kotlin_value
    path.write_text(text.replace(old, old + line, 1), encoding="utf-8")
    print(f"{path}: injected SFA_VARIANT buildConfigField = {variant}")


if __name__ == "__main__":
    main()
