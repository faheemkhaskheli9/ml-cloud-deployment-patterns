"""Tests for the cloud-agnostic inference server."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src import server
from src.model import save_bundle, train_bundle


@pytest.fixture
def client(tmp_path, monkeypatch):
    artifact = tmp_path / "sample_model.joblib"
    save_bundle(train_bundle(), artifact)
    monkeypatch.setenv("MODEL_PATH", str(artifact))
    server._bundle_for.cache_clear()
    yield TestClient(server.app)
    server._bundle_for.cache_clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_model_info(client):
    body = client.get("/model-info").json()
    assert body["feature_names"][0] == "sepal_length_cm"
    assert len(body["target_names"]) == 3


def test_predict_happy_path(client):
    resp = client.post("/predict", json={"instances": [[5.1, 3.5, 1.4, 0.2]]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["predictions"][0]["label"]
    assert body["model_version"] == "sample-iris-1"


def test_predict_wrong_shape_returns_422(client):
    resp = client.post("/predict", json={"instances": [[1.0, 2.0]]})
    assert resp.status_code == 422


def test_predict_empty_instances_rejected(client):
    resp = client.post("/predict", json={"instances": []})
    assert resp.status_code == 422
