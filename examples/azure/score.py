"""Azure ML scoring script entry point (managed online endpoint convention).

Azure ML's inference server imports this module and calls ``init()`` once at
container startup, then ``run(raw_data)`` per request -- see
https://learn.microsoft.com/azure/machine-learning/how-to-deploy-online-endpoints
This is the one file that's Azure-specific; it's a thin adapter over the same
cloud-agnostic ``ModelBundle`` every deployment example (Azure/AWS/GCP) reuses
(``src/model.py``), so the actual prediction logic isn't duplicated per cloud.
"""
from __future__ import annotations

import json
import os

from src.model import ModelBundle, load_bundle

_bundle: ModelBundle | None = None


def init() -> None:
    """Called once when the Azure ML container starts."""
    global _bundle
    # AZUREML_MODEL_DIR is set by the Azure ML runtime to the mounted model
    # artifact's directory; fall back to the local default for a smoke test
    # run outside of Azure ML.
    model_dir = os.environ.get("AZUREML_MODEL_DIR", "models")
    _bundle = load_bundle(os.path.join(model_dir, "sample_model.joblib"))


def run(raw_data: str) -> str:
    """Called once per request with the raw request body as a string."""
    if _bundle is None:
        raise RuntimeError("init() must run before run() (Azure ML calls init() at startup)")
    payload = json.loads(raw_data)
    instances = payload["instances"]
    predictions = _bundle.predict(instances)
    return json.dumps({"predictions": predictions})
