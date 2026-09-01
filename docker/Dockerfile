# Common packaging baseline -- the single source of truth for how the sample
# model + inference server are containerized. Every cloud-specific example
# (docker/azure.Dockerfile, docker/aws.Dockerfile, docker/gcp.Dockerfile) builds
# FROM this image and only adds provider-specific deployment glue.
#
#   docker build -t ml-cloud-deploy-base:latest -f docker/Dockerfile .
#   docker run --rm -p 8000:8000 ml-cloud-deploy-base:latest
#   curl localhost:8000/health

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/models/sample_model.joblib

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Bake the sample model artifact into the image so `docker run` serves it with
# no external download or volume mount.
RUN python -m src.train --output "${MODEL_PATH}"

EXPOSE 8000

# 0.0.0.0 so the container is reachable from the host / cloud load balancer.
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
