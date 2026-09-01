# GCP Vertex AI deployment image -- Phase 4.
# Reuses the common packaging baseline unchanged; only adds Vertex AI serving
# conventions (AIP_HTTP_PORT, health/predict route env vars).
#
#   docker build -t ml-cloud-deploy-base:latest -f docker/Dockerfile .
#   docker build -t ml-cloud-deploy-gcp:latest -f docker/gcp.Dockerfile .

FROM ml-cloud-deploy-base:latest

# Phase 4 will add: Vertex AI env wiring (AIP_HTTP_PORT, AIP_HEALTH_ROUTE,
# AIP_PREDICT_ROUTE) and Workload Identity based access to GCS / Secret Manager.
# The model packaging above is NOT redefined here.
LABEL cloud="gcp" stage="phase-4-planned"
