"""Cloud-agnostic inference server for the sample model.

This is the packaging baseline: every cloud-specific example (Azure ML, AWS
SageMaker, GCP Vertex AI) runs this same server from the same base image and
only differs in how the container is deployed, configured, and given secrets.

    uvicorn src.server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.model import ModelBundle, load_bundle


class PredictRequest(BaseModel):
    # List of samples, each a list of feature values in `feature_names` order.
    instances: list[list[float]] = Field(..., min_length=1)


class Prediction(BaseModel):
    label: str
    label_index: int
    confidence: float


class PredictResponse(BaseModel):
    predictions: list[Prediction]
    model_version: str


@lru_cache(maxsize=1)
def _bundle_for(path: str) -> ModelBundle:
    # Cached on the fully-resolved path so a test can point at its own artifact
    # (robustness rule 11: the cache key is the argument, not a hidden global).
    return load_bundle(path)


def get_bundle() -> ModelBundle:
    return _bundle_for(os.environ.get("MODEL_PATH", "models/sample_model.joblib"))


MODEL_VERSION = os.environ.get("MODEL_VERSION", "sample-iris-1")

app = FastAPI(title="ML Cloud Deployment Patterns - base server", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/model-info")
def model_info() -> dict:
    bundle = get_bundle()
    return {
        "model_version": MODEL_VERSION,
        "feature_names": bundle.feature_names,
        "target_names": bundle.target_names,
    }


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    bundle = get_bundle()
    try:
        results = bundle.predict(req.instances)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PredictResponse(
        predictions=[Prediction(**r) for r in results], model_version=MODEL_VERSION
    )
