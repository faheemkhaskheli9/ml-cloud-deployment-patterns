"""Tests for the sample model bundle."""
from __future__ import annotations

import joblib
import pytest

from src.model import load_bundle, save_bundle, train_bundle


def test_train_and_predict_roundtrip():
    bundle = train_bundle()
    assert bundle.n_features == 4
    preds = bundle.predict([[5.1, 3.5, 1.4, 0.2], [6.7, 3.0, 5.2, 2.3]])
    assert len(preds) == 2
    assert preds[0]["label"] in bundle.target_names
    assert 0.0 <= preds[0]["confidence"] <= 1.0


def test_predict_rejects_wrong_feature_count():
    bundle = train_bundle()
    with pytest.raises(ValueError, match="4 features"):
        bundle.predict([[1.0, 2.0, 3.0]])


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "m.joblib"
    save_bundle(train_bundle(), path)
    assert path.is_file()
    reloaded = load_bundle(path)
    assert reloaded.feature_names == train_bundle().feature_names
    assert reloaded.predict([[5.1, 3.5, 1.4, 0.2]])[0]["label"]


def test_load_missing_artifact_is_hard_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        load_bundle(tmp_path / "absent.joblib")


def test_save_is_atomic_on_failure(tmp_path, monkeypatch):
    path = tmp_path / "m.joblib"
    monkeypatch.setattr(joblib, "dump", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        save_bundle(train_bundle(), path)
    assert not path.exists()
    assert not path.with_suffix(".joblib.tmp").exists()
