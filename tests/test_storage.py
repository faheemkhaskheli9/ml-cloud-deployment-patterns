"""Tests for the object storage abstraction (LocalObjectStorage backend)."""
from __future__ import annotations

import pytest

from src.storage import LocalObjectStorage, ObjectStorage, ObjectStorageError, load_backend


def test_local_backend_satisfies_protocol(tmp_path):
    backend = LocalObjectStorage(tmp_path)
    assert isinstance(backend, ObjectStorage)


def test_upload_then_download_roundtrip(tmp_path):
    backend = LocalObjectStorage(tmp_path / "store")
    src = tmp_path / "model.joblib"
    src.write_bytes(b"fake-model-bytes")

    uri = backend.upload_artifact(src, "models/v1/model.joblib")

    assert uri.startswith("local://")
    assert backend.exists("models/v1/model.joblib")

    dest = tmp_path / "downloaded.joblib"
    result = backend.download_artifact("models/v1/model.joblib", dest)

    assert result == dest
    assert dest.read_bytes() == b"fake-model-bytes"


def test_upload_missing_local_file_raises(tmp_path):
    backend = LocalObjectStorage(tmp_path / "store")
    with pytest.raises(ObjectStorageError):
        backend.upload_artifact(tmp_path / "does-not-exist.bin", "key")


def test_download_missing_key_raises(tmp_path):
    backend = LocalObjectStorage(tmp_path / "store")
    with pytest.raises(ObjectStorageError):
        backend.download_artifact("nope", tmp_path / "out.bin")


def test_exists_false_for_missing_key(tmp_path):
    backend = LocalObjectStorage(tmp_path / "store")
    assert backend.exists("nothing/here") is False


@pytest.mark.parametrize("bad_key", ["/etc/passwd", "../escape", "a/../../b"])
def test_path_traversal_keys_rejected(tmp_path, bad_key):
    backend = LocalObjectStorage(tmp_path / "store")
    with pytest.raises(ObjectStorageError):
        backend.download_artifact(bad_key, tmp_path / "out.bin")


def test_upload_overwrites_existing_key_atomically(tmp_path):
    backend = LocalObjectStorage(tmp_path / "store")
    src1 = tmp_path / "v1.bin"
    src1.write_bytes(b"version-1")
    src2 = tmp_path / "v2.bin"
    src2.write_bytes(b"version-2")

    backend.upload_artifact(src1, "model.bin")
    backend.upload_artifact(src2, "model.bin")

    dest = tmp_path / "out.bin"
    backend.download_artifact("model.bin", dest)
    assert dest.read_bytes() == b"version-2"


def test_load_backend_default_is_local(tmp_path):
    backend = load_backend("local", root_dir=str(tmp_path))
    assert isinstance(backend, LocalObjectStorage)


def test_load_backend_unknown_name_raises():
    with pytest.raises(ValueError):
        load_backend("not-a-real-cloud")
