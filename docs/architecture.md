# Architecture Notes: Cloud ML Deployment Examples

## Pipeline

```text
Model Artifact -> Docker Package -> Cloud-Specific Deployment (Azure/AWS/GCP) -> Object Storage + Secrets Management
```

## Components

- Azure deployment example
- AWS deployment example
- GCP deployment example
- Docker-based packaging
- GPU inference configuration
- Object storage integration
- Secrets/environment configuration patterns

## Object storage abstraction

`src/storage.py` defines the `ObjectStorage` protocol (`upload_artifact`,
`download_artifact`, `exists`) that every cloud example builds on, so
Azure/AWS/GCP-specific deployment code never duplicates artifact-transfer
logic — only the concrete backend differs, selected via `load_backend(name, **kwargs)`.

Backends:

- `LocalObjectStorage` (Phase 1, shipped) — filesystem-backed, used for local
  dev and CI without cloud credentials. Uploads/downloads are atomic (temp
  file + `os.replace`), so a crash mid-copy never leaves a truncated artifact.
- Cloud backends (S3, Azure Blob, GCS) are added in Phases 2-4 behind the same
  protocol; each cloud example picks its backend from config/env, not a code
  branch.

## Design Notes

- Keep provider/model choices swappable behind interfaces (see `multi-llm-router`
  and similar projects in this portfolio for the general pattern).
- Prefer configuration-driven pipelines (YAML/JSON in `configs/`) over hardcoded
  parameters so experiments are reproducible.
