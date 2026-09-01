"""Sample model: a tiny, deterministic sklearn pipeline on the Iris dataset.

Deliberately trivial and CPU-only -- this project is about *packaging and
deployment patterns*, not the model. The same artifact is reused by every
cloud-specific example.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DEFAULT_MODEL_PATH = Path("models/sample_model.joblib")
FEATURE_NAMES = [
    "sepal_length_cm",
    "sepal_width_cm",
    "petal_length_cm",
    "petal_width_cm",
]


@dataclass(frozen=True)
class ModelBundle:
    pipeline: Pipeline
    target_names: list[str]
    feature_names: list[str]

    @property
    def n_features(self) -> int:
        return len(self.feature_names)

    def predict(self, rows: list[list[float]]) -> list[dict]:
        arr = np.asarray(rows, dtype=float)
        if arr.ndim != 2 or arr.shape[1] != self.n_features:
            raise ValueError(
                f"expected each sample to have {self.n_features} features "
                f"({self.feature_names}); got shape {arr.shape}"
            )
        proba = self.pipeline.predict_proba(arr)
        idx = proba.argmax(axis=1)
        return [
            {
                "label": self.target_names[i],
                "label_index": int(i),
                "confidence": float(proba[r, i]),
            }
            for r, i in enumerate(idx)
        ]


def train_bundle(random_state: int = 0) -> ModelBundle:
    data = load_iris()
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=500, random_state=random_state)),
        ]
    )
    pipeline.fit(data.data, data.target)
    return ModelBundle(
        pipeline=pipeline,
        target_names=[str(t) for t in data.target_names],
        feature_names=list(FEATURE_NAMES),
    )


def save_bundle(bundle: ModelBundle, path: str | Path = DEFAULT_MODEL_PATH) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    try:
        joblib.dump(
            {
                "pipeline": bundle.pipeline,
                "target_names": bundle.target_names,
                "feature_names": bundle.feature_names,
            },
            tmp,
        )
        tmp.replace(p)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return p


def load_bundle(path: str | Path = DEFAULT_MODEL_PATH) -> ModelBundle:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(
            f"model artifact not found: {p}. Run `python -m src.train` first "
            f"(the Docker image does this at build time)."
        )
    payload = joblib.load(p)
    return ModelBundle(
        pipeline=payload["pipeline"],
        target_names=[str(t) for t in payload["target_names"]],
        feature_names=list(payload["feature_names"]),
    )
