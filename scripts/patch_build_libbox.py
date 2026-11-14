#!/usr/bin/env python3
"""Prepare build_libbox for a minimal SFA build.

Two source rewrites in cmd/internal/build_libbox/main.go (run from the core repo root):

1. Replace the hardcoded `sharedTags` tag list with the fixed $BUILD_TAGS set.
2. Remove the legacy (API 21) variant build so only the arm64 `libbox.aar` is
   produced (the workflow only needs the standard arm64 AAR).

Both rewrites are best-effort: if a pattern is not found the script reports it
and continues, so an upstream layout change does not silently break the build.
"""
import os
import re
import sys

path = "cmd/internal/build_libbox/main.go"
tags = [t.strip() for t in os.environ.get("BUILD_TAGS", "").split(",") if t.strip()]
if not tags:
    sys.exit("ERROR: BUILD_TAGS is empty")

go_slice = "sharedTags = []string{" + ", ".join('"%s"' % t for t in tags) + "}"

with open(path, encoding="utf-8") as fh:
    lines = fh.read().split("\n")

# --- 1) rewrite sharedTags (drop every `sharedTags = append(sharedTags, ...)` line) ---
out = []
inserted = False
for line in lines:
    stripped = line.lstrip()
    if stripped.startswith("sharedTags = append(sharedTags,"):
        if not inserted:
            indent = line[: len(line) - len(stripped)]
            out.append(indent + go_slice)
            inserted = True
        continue
    out.append(line)
if not inserted:
    sys.exit("ERROR: could not find 'sharedTags = append(sharedTags,' in " + path)
text = "\n".join(out)

# --- 2) remove the legacy (API 21) variant build block ---
legacy_re = re.compile(
    r'\n[ \t]*legacyTags := filterTags\(sharedTags, "with_naive_outbound"\)'
    r"[\s\S]*?\}, bindTarget\)"
)
text, n_legacy = legacy_re.subn("\n", text)
if n_legacy == 0:
    print("WARN: legacy build block not matched; libbox-legacy.aar will still be built (ignored).")

with open(path, "w", encoding="utf-8") as fh:
    fh.write(text)

print("Patched", path)
print("  sharedTags ->", go_slice)
print("  legacy-build removed:", "yes" if n_legacy else "no")
