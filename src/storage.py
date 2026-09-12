"""Object storage abstraction: one interface, swappable cloud backends.

Every cloud-specific example (Azure Blob, AWS S3, GCP Cloud Storage) uploads
and downloads the same model artifact through the :class:`ObjectStorage`
protocol, so the deployment logic never duplicates storage code per cloud --
only the backend construction differs (and that's driven by config/env, not
a code branch per provider).

:class:`LocalObjectStorage` is a filesystem-backed backend used for local
dev and CI (no cloud credentials, no network) -- it mocks the boundary that
real cloud backends (added in later phases) will fill in behind the same
interface. Uploads/downloads are atomic (temp file + ``os.replace``) so a
crash mid-copy never leaves a truncated artifact at the destination.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Protocol, runtime_checkable


class ObjectStorageError(RuntimeError):
    """Raised on a failed upload/download or a missing artifact."""


@runtime_checkable
class ObjectStorage(Protocol):
    """Minimal artifact storage interface every backend must implement."""

    def upload_artifact(self, local_path: str | Path, key: str) -> str:
        """Copy ``local_path`` to the backend under ``key``. Returns a backend URI."""

    def download_artifact(self, key: str, local_path: str | Path) -> Path:
        """Copy the artifact stored under ``key`` to ``local_path``. Returns the path."""

    def exists(self, key: str) -> bool:
        """Return whether an artifact is stored under ``key``."""


class LocalObjectStorage:
    """Filesystem-backed ``ObjectStorage`` — the CI/local-dev backend.

    Stores artifacts under ``root_dir/<key>``. Not a real cloud backend; it
    exists so the storage interface and every caller built against it can be
    exercised without cloud credentials, matching the pattern real backends
    (S3/Blob/GCS) will follow.
    """

    scheme = "local"

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)

    def _path_for(self, key: str) -> Path:
        if not key or key.startswith("/") or ".." in Path(key).parts:
            raise ObjectStorageError(f"invalid artifact key: {key!r}")
        return self.root_dir / key

    def upload_artifact(self, local_path: str | Path, key: str) -> str:
        local_path = Path(local_path)
        if not local_path.is_file():
            raise ObjectStorageError(f"local artifact not found: {local_path}")

        dest = self._path_for(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=dest.parent, prefix=".upload-")
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            shutil.copy2(local_path, tmp)
            tmp.replace(dest)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        return f"{self.scheme}://{dest}"

    def download_artifact(self, key: str, local_path: str | Path) -> Path:
        src = self._path_for(key)
        if not src.is_file():
            raise ObjectStorageError(f"artifact not found under key: {key!r}")

        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=local_path.parent, prefix=".download-")
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            shutil.copy2(src, tmp)
            tmp.replace(local_path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        return local_path

    def exists(self, key: str) -> bool:
        return self._path_for(key).is_file()


def load_backend(name: str = "local", **kwargs) -> ObjectStorage:
    """Config-driven backend construction; add cloud backends here as they land."""
    name = name.lower()
    if name == "local":
        root_dir = kwargs.get("root_dir", "artifacts")
        return LocalObjectStorage(root_dir)
    raise ValueError(f"unknown storage backend: {name!r} (expected 'local' for now)")
