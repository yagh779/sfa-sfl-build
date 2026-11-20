#!/usr/bin/env python3
"""Make the SFA in-app updater fetch variant-specific metadata and APK.

Two coordinated edits to ``GitHubUpdateChecker.kt``:

1. Metadata asset name becomes ``SFA-version-metadata-<variant>.json`` (the
   variant comes from ``BuildConfig.SFA_VARIANT``), so each variant reads its
   own release metadata / version.
2. APK selection prefers the asset whose name embeds this variant's exact
   ``versionName``, then falls back to the variant token, then to the only
   candidate. This keeps per-variant updates correct even when a single
   release carries several variants.
"""

import sys
from pathlib import Path

OLD_META = 'private const val METADATA_FILENAME = "SFA-version-metadata.json"'
NEW_META = (
    'private val METADATA_FILENAME = '
    '"SFA-version-metadata-${BuildConfig.SFA_VARIANT}.json"'
)

OLD_APK = """        val isLegacy = Build.VERSION.SDK_INT < Build.VERSION_CODES.M
        val apkAsset = release.assets.find { asset ->
            asset.name.endsWith(".apk") &&
                !asset.name.contains("play") &&
                asset.name.contains("legacy-android-5") == isLegacy
        }"""

NEW_APK = """        val isLegacy = Build.VERSION.SDK_INT < Build.VERSION_CODES.M
        // A single release may carry several variants: prefer the APK whose name
        // embeds this variant's exact version, then the variant token, then the
        // only remaining candidate.
        val apkCandidates = release.assets.filter { asset ->
            asset.name.endsWith(".apk") &&
                !asset.name.contains("play") &&
                asset.name.contains("legacy-android-5") == isLegacy
        }
        val apkByVersion = apkCandidates.filter {
            metadata.versionName.isNotBlank() && it.name.contains(metadata.versionName, ignoreCase = true)
        }
        val apkPool = apkByVersion.ifEmpty { apkCandidates }
        val apkAsset = apkPool.firstOrNull {
            BuildConfig.SFA_VARIANT.isNotBlank() && it.name.contains(BuildConfig.SFA_VARIANT, ignoreCase = true)
        } ?: apkPool.singleOrNull()"""


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: patch_sfa_update_variant.py <GitHubUpdateChecker.kt>")

    path = Path(sys.argv[1])
    if not path.is_file():
        sys.exit(f"ERROR: file not found: {path}")

    text = path.read_text(encoding="utf-8")

    already = (
        "SFA-version-metadata-${BuildConfig.SFA_VARIANT}.json" in text
        and "apkCandidates" in text
    )
    if already:
        print(f"{path}: already patched for variant metadata + APK selection")
        return

    if text.count(OLD_META) != 1:
        sys.exit(f"ERROR: METADATA_FILENAME constant not found exactly once in {path}")
    if text.count(OLD_APK) != 1:
        sys.exit(
            f"ERROR: APK-selection block not found exactly once in {path} "
            "(upstream source changed?)"
        )

    text = text.replace(OLD_META, NEW_META, 1)
    text = text.replace(OLD_APK, NEW_APK, 1)
    path.write_text(text, encoding="utf-8")
    print(f"{path}: patched variant metadata filename and APK selection")


if __name__ == "__main__":
    main()
