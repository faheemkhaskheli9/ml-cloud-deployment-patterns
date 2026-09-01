"""Train and persist the sample model artifact.

    python -m src.train [--output models/sample_model.joblib]

Called at Docker build time so the base image ships a ready-to-serve artifact.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.model import DEFAULT_MODEL_PATH, save_bundle, train_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="train", description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--random-state", type=int, default=0)
    args = parser.parse_args(argv)

    bundle = train_bundle(random_state=args.random_state)
    path = save_bundle(bundle, args.output)
    print(f"wrote sample model -> {path} ({bundle.n_features} features, "
          f"classes={bundle.target_names})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
