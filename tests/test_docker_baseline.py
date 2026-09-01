"""Enforce the Phase 1 invariant: cloud images reuse the base packaging image.

Acceptance criterion 2 ("each cloud-specific example references this base image
rather than redefining packaging") is checked here rather than left to a
comment (robustness rule 15).
"""
from __future__ import annotations

from pathlib import Path

import pytest

DOCKER_DIR = Path(__file__).resolve().parents[1] / "docker"
BASE_IMAGE = "ml-cloud-deploy-base:latest"
CLOUD_DOCKERFILES = ["azure.Dockerfile", "aws.Dockerfile", "gcp.Dockerfile"]


def test_base_dockerfile_builds_the_artifact_and_serves():
    text = (DOCKER_DIR / "Dockerfile").read_text(encoding="utf-8")
    assert "python -m src.train" in text          # bakes the sample model
    assert "uvicorn" in text and "src.server:app" in text  # serves it
    assert "pip install --no-cache-dir -r requirements.txt" in text


@pytest.mark.parametrize("name", CLOUD_DOCKERFILES)
def test_cloud_dockerfile_reuses_base_image(name):
    text = (DOCKER_DIR / name).read_text(encoding="utf-8")
    assert f"FROM {BASE_IMAGE}" in text, f"{name} must build FROM the base image"
    # It must NOT re-run dependency install or model training itself.
    assert "pip install" not in text, f"{name} redefines packaging"
    assert "src.train" not in text, f"{name} redefines model baking"
