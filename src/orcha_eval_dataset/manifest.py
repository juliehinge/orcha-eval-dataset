from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = 1


class DatasetError(ValueError):
    """Dataset structure or content is invalid."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        while chunk := fp.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_sha256(manifest: dict[str, Any]) -> str:
    return hashlib.sha256(manifest_bytes(manifest)).hexdigest()


def manifest_bytes(manifest: dict[str, Any]) -> bytes:
    return (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()


def _exact_path(root: Path, relative: PurePosixPath) -> Path:
    current = root
    for part in relative.parts:
        matches = {entry.name: entry for entry in current.iterdir()}
        if part not in matches:
            raise DatasetError(f"Path does not exist with exact casing: {relative}")
        current = matches[part]
    if not current.is_file():
        raise DatasetError(f"Expected a file: {relative}")
    return current


def _entry(root: Path, path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256(path),
        "size": path.stat().st_size,
    }


def build_manifest(root: Path) -> dict[str, Any]:
    metadata_dir = root / "metadata"
    files_dir = root / "files"
    if not metadata_dir.is_dir() or not files_dir.is_dir():
        raise DatasetError("Dataset must contain files/ and metadata/ directories")

    records: dict[str, Any] = {}
    referenced_documents: set[str] = set()
    for metadata_path in sorted(metadata_dir.glob("*.json")):
        record_id = metadata_path.stem
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        file_paths = metadata.get("file_paths")
        if not isinstance(file_paths, list) or len(file_paths) != 1:
            raise DatasetError(f"{record_id}: file_paths must contain one path")

        relative = PurePosixPath(file_paths[0])
        if relative.is_absolute() or ".." in relative.parts:
            raise DatasetError(f"{record_id}: invalid PDF path {relative}")
        if len(relative.parts) < 3 or relative.parts[0] != "files":
            raise DatasetError(f"{record_id}: document path must start with files/")
        if relative.suffix.casefold() not in {".pdf", ".png"}:
            raise DatasetError(f"{record_id}: document must be a PDF or PNG")
        document_path = _exact_path(root, relative)
        document_relative = relative.as_posix()
        if document_relative in referenced_documents:
            raise DatasetError(
                f"Document referenced more than once: {document_relative}"
            )
        referenced_documents.add(document_relative)
        records[record_id] = {
            "category": relative.parts[1],
            "document": _entry(root, document_path),
            "metadata": _entry(root, metadata_path),
        }

    all_documents = {
        path.relative_to(root).as_posix()
        for path in files_dir.rglob("*")
        if path.is_file()
    }
    if all_documents != referenced_documents:
        missing = sorted(all_documents - referenced_documents)
        absent = sorted(referenced_documents - all_documents)
        raise DatasetError(
            f"Document inventory mismatch; unreferenced={missing}, missing={absent}"
        )

    return {"schema_version": SCHEMA_VERSION, "records": records}


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise DatasetError(
            f"Unsupported manifest schema: {manifest.get('schema_version')}"
        )
    if not isinstance(manifest.get("records"), dict):
        raise DatasetError("Manifest records must be an object")
    return manifest


def check_manifest(root: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    path = manifest_path or root / "manifest.json"
    stored = load_manifest(path)
    actual = build_manifest(root)
    if stored != actual:
        raise DatasetError("manifest.json does not match the dataset")
    return stored


def manifest_paths(manifest: dict[str, Any]) -> list[str]:
    paths = []
    for record in manifest["records"].values():
        paths.extend((record["document"]["path"], record["metadata"]["path"]))
    return sorted(paths)
