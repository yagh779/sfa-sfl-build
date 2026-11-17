#!/usr/bin/env python3
"""Pin the Linux desktop (SFL) package identity to fixed values.

Patches a desktop client directory so its .deb always keeps the SAME package
name / identity, regardless of which variant (reF1nd vs MiChongs) it is built
from. This lets the two variants be installed over each other.

Touched files inside <desktop_dir>:
  * package.json       -> "name", "desktopName"   (the deb `Package:` comes from "name")
  * electron-builder.yml -> top-level appId / productName,
                            linux.appId / linux.executableName

Usage: python3 pin_desktop_package_name.py <desktop_dir>
Idempotent.
"""

import json
import os
import re
import sys

PKG_NAME = "sing-box-for-desktop-ref1nd"
DESKTOP_NAME = "sing-box-reF1nd.desktop"
APP_ID = "io.github.reF1nd.sing-box-desktop"
PRODUCT = "sing-box-reF1nd"
LINUX_APP_ID = "io.reF1nd.sfl"
EXE = "sing-box-reF1nd"


def patch_package_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    changes = []
    if data.get("name") != PKG_NAME:
        changes.append(("name", data.get("name")))
        data["name"] = PKG_NAME
    if data.get("desktopName") != DESKTOP_NAME:
        changes.append(("desktopName", data.get("desktopName")))
        data["desktopName"] = DESKTOP_NAME
    if changes:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    return changes


def patch_electron_builder(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()

    lines = text.splitlines()
    out = []
    in_linux = False
    changes = []
    for line in lines:
        is_top = bool(line) and not line[0].isspace()
        if is_top:
            in_linux = (line.strip() == "linux:")

        if not in_linux:
            if re.match(r"^appId:\s", line):
                if line != f"appId: {APP_ID}":
                    changes.append(("appId", line))
                    line = f"appId: {APP_ID}"
            elif re.match(r"^productName:\s", line):
                if line != f"productName: {PRODUCT}":
                    changes.append(("productName", line))
                    line = f"productName: {PRODUCT}"
        else:
            m = re.match(r"^(\s+)appId:\s", line)
            if m:
                if line != f"{m.group(1)}appId: {LINUX_APP_ID}":
                    changes.append(("linux.appId", line))
                    line = f"{m.group(1)}appId: {LINUX_APP_ID}"
            m2 = re.match(r"^(\s+)executableName:\s", line)
            if m2:
                if line != f"{m2.group(1)}executableName: {EXE}":
                    changes.append(("linux.executableName", line))
                    line = f"{m2.group(1)}executableName: {EXE}"
        out.append(line)

    if changes:
        new_text = "\n".join(out)
        if text.endswith("\n"):
            new_text += "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
    return changes


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: pin_desktop_package_name.py <desktop_dir>", file=sys.stderr)
        return 2
    d = sys.argv[1]
    pkg = os.path.join(d, "package.json")
    eb = os.path.join(d, "electron-builder.yml")
    for p in (pkg, eb):
        if not os.path.isfile(p):
            print(f"::error::not found: {p}", file=sys.stderr)
            return 1

    pj = patch_package_json(pkg)
    eb_changes = patch_electron_builder(eb)

    for key, old in pj:
        print(f'package.json: {key}: {old!r} -> pinned')
    for key, old in eb_changes:
        print(f"electron-builder.yml: {key}: {old.strip()!r} -> pinned")
    if not pj and not eb_changes:
        print("already pinned: desktop package identity unchanged")
    else:
        print("pinned desktop package identity to fixed values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
