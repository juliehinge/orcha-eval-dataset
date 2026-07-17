# Orcha evaluation dataset

This repository contains the fixed evaluation dataset for Orcha's
bibliographic metadata extraction pipeline.
It pairs 181 scholarly documents with manually curated JSON ground truth.

The 179 PDFs and two PNG posters live in Git LFS.
Metadata and `manifest.json` are regular Git files,
so checking the current inventory does not consume LFS bandwidth.

## Layout

```text
files/<category>/*.{pdf,png}
metadata/<record_id>.json
manifest.json
```

Each metadata file points to one PDF through `file_paths`.
Paths are case-sensitive and start with `files/`.
The manifest records each file's path, byte size, and SHA-256 hash.

Generated extraction text, experiment results, and intake files are excluded.

## Local setup

Install Git LFS before cloning or committing documents:

```bash
brew install git-lfs
git lfs install
uv sync
```

Rebuild and check the manifest after changing PDFs or metadata:

```bash
uv run python3 scripts/build_manifest.py
uv run python3 scripts/check_dataset.py
git lfs fsck
```

Commit `manifest.json` with the dataset changes.

## Zenodo publishing

The repository does not use the Zenodo GitHub integration.
The publishing script creates a deterministic ZIP,
uploads it with a separate `manifest.json`,
and publishes either a new Zenodo record or a new version.

Test against Zenodo Sandbox first:

```bash
ZENODO_SANDBOX_TOKEN=... \
  uv run python3 scripts/publish_zenodo.py --sandbox --draft
```

Publish to Zenodo:

```bash
ZENODO_TOKEN=... uv run python3 scripts/publish_zenodo.py
```

The token needs `deposit:write` and `deposit:actions` scopes.
The first production publish writes `.zenodo-record.json`.
Commit that file so later runs create versions under the same concept DOI.
Unchanged manifests are skipped unless `--force` is passed.

## Retrieval model

Consumers download the latest published ZIP from Zenodo to seed a local
content-addressed cache.
They then read the small manifest from GitHub at one resolved commit
and download only missing document hashes from GitHub LFS.
Repeated evaluations reuse the cache.

From the evaluation repository:

```bash
uv run python3 -m evals.dataset_sync
uv run python3 -m evals.local_run \
  --sync-dataset \
  --model <provider/model> \
  --run-name <slug> \
  --mode tool
```

Evaluation provenance includes the Git commit,
manifest SHA-256, Zenodo record ID, and dataset release version.

## Redistribution rights

The dataset contains third-party PDFs.
Their source licenses must permit redistribution before the production Zenodo
record and GitHub repository are made public.
A repository license does not replace the rights attached to each PDF.
