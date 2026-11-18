#!/usr/bin/env python3
"""Emit the GitHub Actions matrices for build-sfa-sfl.yml.

Scope (per user decision):
  * SFA  -> Android arm64 only, `other` flavor only (no legacy).
  * SFL  -> Linux amd64 only, `.deb` only.

The version is supplied per variant (version_xiaobaf14g / version_ref1nd) so the
two variants can carry independent version numbers; it only affects naming and
metadata, never which commit is built.
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
        sys.exit(f"ERROR: missing version for variant(s): {', '.join(missing)}")

    sfa, sfl, prep, meta = [], [], [], []

    # When two variants are built together and carry the SAME version string, their
    # artifact file names would collide once the variant suffix is dropped. In that
    # case re-append the "-<variant>" suffix to keep the names unique.
    versions = [version_of[c["variant"]] for c in selected]
    need_variant_suffix = len(selected) > 1 and len(set(versions)) == 1
    if need_variant_suffix:
        print(
            "NOTE: both variants share the same version; artifact names will include "
            "the '-<variant>' suffix to avoid a file-name collision",
            file=sys.stderr,
        )

    for c in selected:
        v = version_of[c["variant"]]
        suffix = f"-{c['variant']}" if need_variant_suffix else ""
        meta.append({**c, "version": v})
        # prepare: one entry per variant, warms the shared Go module cache.
        prep.append({
            "variant": c["variant"],
            "core_repo": c["core_repo"],
            "core_ref": c["core_ref"],
        })
        # SFA: arm64 only, standard (non-legacy) flavor.
        sfa.append({**c, "version": v, "name_suffix": suffix, "flavor": "other", "task": ":app:assembleOtherRelease"})
        # SFL: amd64 only, deb package.
        sfl.append({
            **c,
            "version": v,
            "name_suffix": suffix,
            "desktop_arch": "x64",
            "go_arch": "amd64",
            "rust_target": "x86_64-unknown-linux-gnu",
        })

    # Release tag base: everything before the last "-" of the version,
    # regardless of variant (e.g. "1.15.0-alpha-reF1nd.11" -> "1.15.0-alpha").
    # For variant=both the per-variant bases must agree so both share one Release.
    bases = {m["version"].rsplit("-", 1)[0] for m in meta}
    if len(bases) != 1:
        sys.exit(f"ERROR: versions map to different release tags: {', '.join(sorted(bases))}")
    base = bases.pop()
    # Tag: variant=both uses the bare base; a single variant appends its name.
    tag = base if len(meta) > 1 else f"{base}-{meta[0]['variant']}"

    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
        fh.write("prepare=" + json.dumps(prep) + "\n")
        fh.write("sfa=" + json.dumps(sfa) + "\n")
        fh.write("sfl=" + json.dumps(sfl) + "\n")
        fh.write("meta=" + json.dumps(meta) + "\n")
        fh.write("tag=" + tag + "\n")


if __name__ == "__main__":
    main()
