#!/usr/bin/env python3
"""Emit the GitHub Actions matrices for build-sfa-sfl.yml.

Reads VARIANT and VERSION from the environment (set from workflow_dispatch
inputs) and appends `sfa`, `sfl` and `tag` to $GITHUB_OUTPUT.

Scope (per user decision):
  * SFA  -> Android arm64 only, `other` flavor only (no legacy).
  * SFL  -> Linux amd64 only, `.deb` only.
"""
import json
import os

# Per-variant source coordinates. Edit here if a ref moves.
VARIANTS = {
    "xiaobaf14g": {
        "variant": "xiaobaf14g",
        "core_repo": "MiChongs/sing-box",
        "core_ref": "xiaobaf14g-testing",
        "sfa_repo": "MiChongs/sing-box-for-android",
        "sfa_ref": "xiaobaf14g-testing",
        "sfl_repo": "MiChongs/sing-box-for-desktop",
        "sfl_ref": "xiaobaf14g-dev",
    },
    "reF1nd": {
        "variant": "reF1nd",
        "core_repo": "reF1nd/sing-box",
        "core_ref": "reF1nd-testing-next",
        "sfa_repo": "reF1nd/sing-box-for-android",
        "sfa_ref": "reF1nd-testing",
        "sfl_repo": "reF1nd/sing-box-for-desktop",
        "sfl_ref": "reF1nd-dev",
    },
}


def main() -> None:
    variant = os.environ["VARIANT"].strip()
    version = os.environ["VERSION"].strip().lstrip("v")

    if variant == "both":
        selected = list(VARIANTS.values())
    else:
        selected = [VARIANTS[variant]]

    sfa, sfl = [], []
    for c in selected:
        # SFA: arm64 only, standard (non-legacy) flavor.
        sfa.append({**c, "flavor": "other", "task": ":app:assembleOtherRelease"})
        # SFL: amd64 only, deb package.
        sfl.append({
            **c,
            "desktop_arch": "x64",
            "go_arch": "amd64",
            "rust_target": "x86_64-unknown-linux-gnu",
        })

    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
        fh.write("sfa=" + json.dumps(sfa) + "\n")
        fh.write("sfl=" + json.dumps(sfl) + "\n")
        fh.write("tag=sfa-sfl-v" + version + "\n")


if __name__ == "__main__":
    main()
