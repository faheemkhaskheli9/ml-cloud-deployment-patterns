# Azure ML deployment image -- Phase 2.
# Reuses the common packaging baseline unchanged; only adds Azure-specific
# deployment glue (scoring wrapper / entry script conventions).
#
#   docker build -t ml-cloud-deploy-base:latest -f docker/Dockerfile .
#   docker build -t ml-cloud-deploy-azure:latest -f docker/azure.Dockerfile .

FROM ml-cloud-deploy-base:latest

# Phase 2 will add: Azure ML inference entry-script shim, AZUREML_* env wiring,
# and Managed Identity based access to blob storage / Key Vault. The model
# packaging above is NOT redefined here.
LABEL cloud="azure" stage="phase-2-planned"
