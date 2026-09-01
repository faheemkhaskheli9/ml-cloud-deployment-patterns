# AWS SageMaker deployment image -- Phase 3.
# Reuses the common packaging baseline unchanged; only adds SageMaker-specific
# serving conventions (the /ping and /invocations contract, `serve` entrypoint).
#
#   docker build -t ml-cloud-deploy-base:latest -f docker/Dockerfile .
#   docker build -t ml-cloud-deploy-aws:latest -f docker/aws.Dockerfile .

FROM ml-cloud-deploy-base:latest

# Phase 3 will add: SageMaker `serve` entrypoint mapping /ping -> /health and
# /invocations -> /predict, plus IAM-role based access to S3 / Secrets Manager.
# The model packaging above is NOT redefined here.
LABEL cloud="aws" stage="phase-3-planned"
