from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from orcha_eval_dataset.manifest import check_manifest, manifest_sha256


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate dataset files and manifest.")
    parser.add_argument("--root", type=Path, default=Path(__file__).parent.parent)
    args = parser.parse_args()

    manifest = check_manifest(args.root)
    categories = Counter(record["category"] for record in manifest["records"].values())
    print(f"Validated {len(manifest['records'])} records")
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count}")
    print(f"Manifest sha256: {manifest_sha256(manifest)}")


if __name__ == "__main__":
    main()
