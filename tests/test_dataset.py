import json
from pathlib import Path

import pytest

from orcha_eval_dataset.archive import build_archive
from orcha_eval_dataset.manifest import DatasetError, build_manifest, manifest_bytes


def make_dataset(root: Path, pdf_path: str = "files/Articles/ART_1.pdf") -> None:
    (root / "files/Articles").mkdir(parents=True)
    (root / "metadata").mkdir()
    (root / "files/Articles/ART_1.pdf").write_bytes(b"pdf")
    (root / "metadata/ART_1.json").write_text(
        json.dumps({"title": "Example", "file_paths": [pdf_path]}),
        encoding="utf-8",
    )


def test_manifest_records_content_hashes(tmp_path: Path) -> None:
    make_dataset(tmp_path)

    manifest = build_manifest(tmp_path)

    assert manifest == {
        "schema_version": 1,
        "records": {
            "ART_1": {
                "category": "Articles",
                "document": {
                    "path": "files/Articles/ART_1.pdf",
                    "sha256": (
                        "c35b21d6ca39aa7cc3b79a705d989f1a6e88b99ab43988d7404879"
                        "9e3db926a3"
                    ),
                    "size": 3,
                },
                "metadata": {
                    "path": "metadata/ART_1.json",
                    "sha256": (
                        "1e7582f23fa5389a1b2808238fd7c7e40534c3648ea010a081b4b0"
                        "4557894131"
                    ),
                    "size": 64,
                },
            }
        },
    }


def test_manifest_rejects_wrong_path_case(tmp_path: Path) -> None:
    make_dataset(tmp_path, "Files/Articles/ART_1.pdf")

    with pytest.raises(DatasetError, match="must start with files/"):
        build_manifest(tmp_path)


def test_archive_is_byte_stable(tmp_path: Path) -> None:
    make_dataset(tmp_path)
    manifest = build_manifest(tmp_path)
    (tmp_path / "manifest.json").write_bytes(manifest_bytes(manifest))

    first = build_archive(tmp_path, manifest, tmp_path / "first.zip")
    second = build_archive(tmp_path, manifest, tmp_path / "second.zip")

    assert first.read_bytes() == second.read_bytes()
