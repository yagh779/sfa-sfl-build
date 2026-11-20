#!/usr/bin/env python3
"""Point a client's in-app update checker at a GitHub Releases API URL.

The SFA (Android) client keeps the endpoint in
``app/src/github/java/io/nekohasekai/sfa/vendor/GitHubUpdateChecker.kt`` as
``RELEASES_URL`` and the SFL (desktop) client keeps it in ``src/main/updates.ts``
as ``const RELEASES_URL``. Both are rewritten to the value passed in.
"""

import re
import sys
from pathlib import Path

PATTERN = re.compile(r'(RELEASES_URL\s*=\s*)"[^"]*"')


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: patch_update_url.py <file> <releases_api_url>")

    path = Path(sys.argv[1])
    url = sys.argv[2].strip()
    if not url:
        sys.exit("ERROR: empty releases URL")
    if not path.is_file():
        sys.exit(f"ERROR: file not found: {path}")

    text = path.read_text(encoding="utf-8")
    found = PATTERN.findall(text)
    if len(found) != 1:
        sys.exit(
            f"ERROR: expected exactly one RELEASES_URL assignment in {path}, "
            f"found {len(found)}"
        )

    new_text = PATTERN.sub(lambda m: f'{m.group(1)}"{url}"', text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")

    match = PATTERN.search(new_text)
    if match is None or f'"{url}"' not in match.group(0):
        sys.exit(f"ERROR: failed to set RELEASES_URL in {path}")

    print(f"patched {path}: {match.group(0).strip()}")


if __name__ == "__main__":
    main()
