#!/usr/bin/env python3
"""Emit the GitHub Actions matrices for build-sfa-sfl.yml.

Reads VARIANT, VERSION_XIAOBAF14G, VERSION_REF1ND from the environment and
appends `prepare`, `sfa`, `sfl`, `meta` and `tag` to $GITHUB_OUTPUT.

Each variant carries ITS OWN version (reF1nd and xiaobaf14g/MiChongs may be at
different versions), so the single-version limitation is removed. A version is
required only for the variants actually selected.

Scope (per user decision):
  * SFA  -> Android arm64 only, `other` flavor only (no legacy).
  * SFL  -> Linux amd64 only, `.deb` only.
"""
import json
import os
import sys

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
    version_of = {
        "xiaobaf14g": os.environ.get("VERSION_XIAOBAF14G", "").strip().lstrip("v"),
        "reF1nd": os.environ.get("VERSION_REF1ND", "").strip().lstrip("v"),
    }

    if variant == "both":
        selected = [VARIANTS["xiaobaf14g"], VARIANTS["reF1nd"]]
    else:
        selected = [VARIANTS[variant]]

    missing = [c["variant"] for c in selected if not version_of[c["variant"]]]
    if missing:
        sys.exit("ERROR: missing version for variant(s): " + ", ".join(missing))

    sfa, sfl, prep, meta = [], [], [], []
    for c in selected:
        v = version_of[c["variant"]]
        meta.append({**c, "version": v})
        # prepare: one entry per variant, warms the shared Go module cache.
        prep.append({
            "variant": c["variant"],
            "core_repo": c["core_repo"],
            "core_ref": c["core_ref"],
        })
        # SFA: arm64 only, standard (non-legacy) flavor.
        sfa.append({**c, "version": v, "flavor": "other", "task": ":app:assembleOtherRelease"})
        # SFL: amd64 only, deb package.
        sfl.append({
            **c,
            "version": v,
            "desktop_arch": "x64",
            "go_arch": "amd64",
            "rust_target": "x86_64-unknown-linux-gnu",
        })

    # Release tag encodes every variant's own version: sfa-sfl-<variant>-<ver>...
    tag = "sfa-sfl-" + "-".join("%s-%s" % (m["variant"], m["version"]) for m in meta)

    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
        fh.write("prepare=" + json.dumps(prep) + "\n")
        fh.write("sfa=" + json.dumps(sfa) + "\n")
        fh.write("sfl=" + json.dumps(sfl) + "\n")
        fh.write("meta=" + json.dumps(meta) + "\n")
        fh.write("tag=" + tag + "\n")


if __name__ == "__main__":
    main()
