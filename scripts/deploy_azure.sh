#!/usr/bin/env bash
# Step-by-step Azure ML managed online endpoint deployment (Phase 2 example).
#
# This script documents the real `az ml` commands an operator with an Azure
# subscription and the `ml` CLI extension would run. It is NOT executed by
# CI or by any test in this repo -- no Azure credentials are available in
# this sandbox, and none are ever hardcoded here (see .env.example / Phase 2
# secrets-pattern issue for how credentials are actually supplied).
#
# Validate the YAML configs offline first (no credentials needed):
#   python -m src.main azure-plan --endpoint examples/azure/endpoint.yaml \
#       --deployment examples/azure/deployment.yaml
set -euo pipefail

RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:?set AZURE_RESOURCE_GROUP}"
WORKSPACE="${AZURE_ML_WORKSPACE:?set AZURE_ML_WORKSPACE}"
ACR_NAME="${AZURE_ACR_NAME:?set AZURE_ACR_NAME}"

echo "1. Log in (interactive or via a service principal already configured in the environment)."
az login --output none

echo "2. Build and push the Azure-specific image to your Azure Container Registry."
docker build -t "${ACR_NAME}.azurecr.io/ml-cloud-deploy-azure:latest" -f docker/azure.Dockerfile .
az acr login --name "${ACR_NAME}"
docker push "${ACR_NAME}.azurecr.io/ml-cloud-deploy-azure:latest"

echo "3. Create the managed online endpoint (idempotent: safe to re-run)."
az ml online-endpoint create \
  --file examples/azure/endpoint.yaml \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${WORKSPACE}"

echo "4. Create the deployment behind that endpoint."
echo "   Gotcha: this is where quota errors surface, not at YAML validation time --"
echo "   see docs/architecture.md 'Azure ML deployment (Phase 2)' for the quota note."
az ml online-deployment create \
  --file examples/azure/deployment.yaml \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${WORKSPACE}"

echo "5. Smoke-test at 0% traffic before shifting any live traffic to it."
az ml online-endpoint invoke \
  --name ml-cloud-deploy-endpoint \
  --request-file examples/azure/sample_request.json \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${WORKSPACE}"

echo "6. Once verified, shift traffic (e.g. 100% to this deployment)."
az ml online-endpoint update \
  --name ml-cloud-deploy-endpoint \
  --traffic "blue=100" \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${WORKSPACE}"
