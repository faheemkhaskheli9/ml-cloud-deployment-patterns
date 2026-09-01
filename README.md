# Cloud ML Deployment Examples

> AI Infrastructure / Deployment portfolio project — independent open-source implementation.
> This is an original, from-scratch build. It is not affiliated with, and does not
> contain any code, prompts, data, or business logic from, any employer or client.

![status](https://img.shields.io/badge/status-in%20progress-yellow)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

## 1. Problem

ML deployment patterns differ meaningfully across cloud providers; a reference set of examples helps teams choose and migrate confidently.

## 2. Architecture

```text
Model Artifact -> Docker Package -> Cloud-Specific Deployment (Azure/AWS/GCP) -> Object Storage + Secrets Management
```

## 3. Technology Stack

- Docker
- Azure ML / AWS SageMaker / GCP Vertex AI
- Terraform (optional IaC)
- Python

## 4. Feature List

- Azure deployment example
- AWS deployment example
- GCP deployment example
- Docker-based packaging
- GPU inference configuration
- Object storage integration
- Secrets/environment configuration patterns

## 5. Implementation Plan

1. Phase 1: Common Docker packaging baseline
2. Phase 2: Azure ML deployment example
3. Phase 3: AWS SageMaker deployment example
4. Phase 4: GCP Vertex AI deployment example

## 6. Repository Structure

```text
ml-cloud-deployment-patterns/
├── README.md
├── LICENSE
├── .gitignore
├── pyproject.toml
├── .env.example
├── docker/
├── docs/
│   ├── architecture.md
│   └── evaluation.md
├── src/
├── tests/
├── configs/
├── scripts/
├── notebooks/
├── examples/
├── assets/
└── .github/
    └── workflows/
```

## 7. Setup

```bash
git clone <this-repo-url>
cd ml-cloud-deployment-patterns
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # or: pip install -e .
cp .env.example .env              # fill in API keys / config
```

## 8. Dataset

Document which public dataset(s) or synthetic data generators are used here.
No proprietary, employer-owned, or client-identifiable data is used in this project.

## 9. Training / Execution

Document the commands used to run training, ingestion, or the main pipeline, e.g.:

```bash
python -m src.main --config configs/default.yaml
```

## 10. Evaluation

Document evaluation metrics and how to reproduce them here (see `docs/evaluation.md`).

## 11. Results

_To be filled in as the implementation progresses — screenshots, metrics tables, and
sample outputs go here._

## 12. API

_If this project exposes an API, document the main endpoints here (or link to
auto-generated OpenAPI docs, e.g. `/docs` for FastAPI)._

## 13. Docker

### Common packaging baseline (Phase 1)

`docker/Dockerfile` is the single source of truth for packaging the sample
model + inference server. It installs `requirements.txt`, copies `src/`, bakes
the sample model artifact into the image at build time (`python -m src.train`),
and serves it with uvicorn on port 8000.

```bash
docker build -t ml-cloud-deploy-base:latest -f docker/Dockerfile .
docker run --rm -p 8000:8000 ml-cloud-deploy-base:latest

curl localhost:8000/health
curl -X POST localhost:8000/predict \
  -H 'content-type: application/json' \
  -d '{"instances": [[5.1, 3.5, 1.4, 0.2]]}'
```

### Cloud-specific images

Each provider example builds **`FROM ml-cloud-deploy-base:latest`** and only adds
deployment glue — it never re-installs dependencies or re-bakes the model:

| File | Cloud | Phase |
|------|-------|-------|
| `docker/azure.Dockerfile` | Azure ML | 2 |
| `docker/aws.Dockerfile` | AWS SageMaker | 3 |
| `docker/gcp.Dockerfile` | GCP Vertex AI | 4 |

### Run the server without Docker

```bash
python -m src.train                       # writes models/sample_model.joblib
uvicorn src.server:app --port 8000        # then open http://127.0.0.1:8000/docs
```

## 14. Tests

```bash
pytest tests/
```

## 15. Limitations

- This is a from-scratch, independent recreation built for portfolio purposes.
- Performance numbers, once added, are based on public datasets and are not
  representative of any production system's real-world results.

## 16. Future Work

- Expand evaluation coverage and add CI-based regression checks.
- Add more configuration presets and deployment targets.
- Track open items as GitHub Issues.

## 17. Disclosure

This repository is an **independent open-source recreation inspired by the kind of
production systems I have worked on professionally**. It contains no employer or
client source code, prompts, datasets, credentials, architecture diagrams, or
business logic. All code, data, and documentation here are original or built on
publicly available datasets and open-source tools.

---
_Last updated: 2026-08-18_
