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

## Azure ML deployment (Phase 2)

`examples/azure/` holds a documented, declarative example of deploying the
base Docker image (`docker/azure.Dockerfile`) to an Azure ML **managed
online endpoint**:

- `endpoint.yaml` / `deployment.yaml` — Azure ML CLI v2 schema, consumed by
  both the real `az ml online-endpoint/online-deployment create` commands
  and by this repo's own offline validator.
- `score.py` — the Azure ML scoring script convention (`init()` once at
  container startup, `run(raw_data)` per request), a thin adapter over the
  same cloud-agnostic `ModelBundle` (`src/model.py`) every cloud example reuses.
- `sample_request.json` — a smoke-test payload for `az ml online-endpoint invoke`.

`scripts/deploy_azure.sh` documents the full step-by-step `az` CLI sequence
an operator with a real Azure subscription would run (login, build/push to
ACR, create endpoint, create deployment, smoke-test, shift traffic). It is
not executed by CI or tests — this sandbox has no Azure credentials — and it
never hardcodes any (see `.env.example` for the Azure secrets pattern).

`src/azure_deploy.py` validates `endpoint.yaml`/`deployment.yaml` **offline**
(no Azure SDK call, no network) and produces a dry-run deployment plan:

```bash
python -m src.main azure-plan --endpoint examples/azure/endpoint.yaml \
    --deployment examples/azure/deployment.yaml
```

### Azure-specific gotchas recorded here

- **Endpoint/deployment names** are lowercase alphanumeric + hyphens, must
  start with a letter, 3-32 chars — a name that violates this is rejected by
  `az ml` at creation time with a schema error, not earlier; the validator
  above catches it before that round trip.
- **Online-deployment quota is a separate pool from your regular VM quota**,
  charged per `(instance_type, region)` and small by default. A deployment
  sized above it passes YAML validation but fails at
  `az ml online-deployment create` — request a quota increase in advance.
  The validator flags known instance types whose total requested vCPUs look
  large, and flags any instance type outside its small reference table so
  you check it against your subscription before deploying.
- **First rollout should not be at 100% traffic.** Deploy at 0%, smoke-test
  the endpoint directly (`az ml online-endpoint invoke`), then shift traffic
  with `az ml online-endpoint update` once verified. The validator warns if
  `traffic_percentage: 100` is set on a config being planned for the first time.

## Design Notes

- Keep provider/model choices swappable behind interfaces (see `multi-llm-router`
  and similar projects in this portfolio for the general pattern).
- Prefer configuration-driven pipelines (YAML/JSON in `configs/`) over hardcoded
  parameters so experiments are reproducible.
