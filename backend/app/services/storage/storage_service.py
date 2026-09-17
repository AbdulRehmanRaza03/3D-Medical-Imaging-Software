"""Structured storage for binary medical artifacts.

All pixel/mesh/mask data is persisted here rather than in database rows (the
DB stores only metadata + a reference/path). This module provides a single
``storage_service`` instance used throughout the application.

Backends
--------
- ``local`` (default): filesystem under ``STORAGE_DIR``.
- ``s3``: S3-compatible object storage (Supabase Storage, Cloudflare R2, AWS
  S3, MinIO). Requires ``boto3`` (declared as an optional dependency in
  ``requirements-storage.txt``).

Layout (identical for both backends)::

    studies/{study_id}/
        dicom/                # original uploaded DICOM files
        volume/volume.npz     # constructed 3D CT volume + spatial metadata
        models/{model_id}.npz # reconstructed mesh (vertices + faces)
        segmentations/{result_id}.npz

The object-storage backend mirrors this directory structure as object keys so
that switching between backends does not require renaming stored data.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.core.exceptions import ProcessingError, NotFoundError

logger = logging.getLogger(__name__)


def _local_storage_dir() -> Path:
    """Absolute path of the root storage directory on the local filesystem."""
    path = Path(settings.storage_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _local_study_dir(study_id: int) -> Path:
    d = _local_storage_dir() / "studies" / str(study_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def volume_dir(study_id: int) -> Path:
    """Directory where a study's constructed volume is stored (local backend)."""
    if settings.storage_backend != "local":
        # Object storage has no real directories; this helper is only valid for
        # the local backend. Callers that only glob for volume files must go
        # through ``storage_service`` when using S3.
        raise ProcessingError(
            "volume_dir() is only available with the local storage backend.",
            code="storage_backend_mismatch",
        )
    return _ensure_dir(_local_study_dir(study_id) / "volume")


class _LocalStorage:
    """Filesystem-backed storage."""

    backend = "local"

    def save_dicom_files(self, study_id: int, files: list[tuple[str, bytes]]) -> None:
        d = _ensure_dir(_local_study_dir(study_id) / "dicom")
        for fname, data in files:
            # Sanitize filenames against path traversal.
            safe = os.path.basename(fname) or "unnamed.dcm"
            (d / safe).write_bytes(data)
        logger.info("Saved %d DICOM files for study %d", len(files), study_id)

    def save_volume(self, study_id: int, buf: bytes, filename: str = "volume.npz") -> str:
        d = volume_dir(study_id)
        path = d / filename
        path.write_bytes(buf)
        return str(path)

    def load_volume(self, study_id: int):
        d = volume_dir(study_id)
        candidates = sorted(d.glob("*.npz"))
        if not candidates:
            raise NotFoundError("Volume not found for study.", code="volume_missing")
        return np.load(candidates[0], allow_pickle=False)

    def save_model_mesh(self, study_id: int, vertices: np.ndarray, faces: np.ndarray) -> str:
        d = _ensure_dir(_local_study_dir(study_id) / "models")
        # Use a monotonically increasing suffix based on existing files.
        existing = list(d.glob("*.npz"))
        model_index = len(existing) + 1
        path = d / f"{model_index}.npz"
        np.savez_compressed(path, vertices=vertices, faces=faces)
        return str(path)

    def load_model_mesh(self, mesh_path: str) -> tuple[np.ndarray, np.ndarray]:
        path = Path(mesh_path)
        if not path.exists():
            raise NotFoundError("Mesh file not found.", code="mesh_missing")
        loaded = np.load(path, allow_pickle=False)
        return loaded["vertices"], loaded["faces"]

    def save_segmentation_mask(self, study_id: int, mask: np.ndarray) -> str:
        d = _ensure_dir(_local_study_dir(study_id) / "segmentations")
        existing = list(d.glob("*.npz"))
        idx = len(existing) + 1
        path = d / f"{idx}.npz"
        np.savez_compressed(path, mask=mask)
        return str(path)

    def load_segmentation_mask(self, mask_path: str) -> np.ndarray:
        path = Path(mask_path)
        if not path.exists():
            raise NotFoundError("Segmentation mask not found.", code="mask_missing")
        return np.load(path, allow_pickle=False)["mask"]


class _S3Storage:
    """S3-compatible object storage backed by boto3.

    Object keys mirror the local directory layout so data is portable between
    backends. The client is created lazily so importing this module does not
    require boto3 unless the backend is actually configured to use S3.
    """

    backend = "s3"

    def __init__(self) -> None:
        try:
            import boto3  # noqa: F401
        except ImportError as exc:  # pragma: no cover - depends on env
            raise ProcessingError(
                "S3 storage backend requires the 'boto3' package. "
                "Install it with: pip install -r requirements-storage.txt",
                code="storage_dependency_missing",
            ) from exc

        self._bucket = settings.s3_bucket_name
        if not self._bucket:
            raise ProcessingError(
                "S3 storage backend requires S3_BUCKET_NAME to be set.",
                code="storage_config_missing",
            )
        # S3 bucket names disallow spaces and uppercase; fail fast with a clear
        # message instead of a cryptic boto3 validation error at request time.
        import re

        if not re.match(r"^[a-z0-9.\-_]+$", self._bucket):
            raise ProcessingError(
                "Invalid S3_BUCKET_NAME. Bucket names must be lowercase and may "
                "contain only letters, numbers, dots, dashes, or underscores "
                "(no spaces).",
                code="storage_config_invalid",
            )

    def _client(self):
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            region_name=settings.s3_region or None,
            aws_access_key_id=settings.s3_access_key or None,
            aws_secret_access_key=settings.s3_secret_key or None,
        )

    def _key(self, *parts: str) -> str:
        return "/".join(str(p) for p in parts)

    def _put(self, key: str, data: bytes) -> str:
        self._client().put_object(Bucket=self._bucket, Key=key, Body=data)
        return key

    def _get_bytes(self, key: str) -> bytes:
        import botocore.exceptions

        try:
            obj = self._client().get_object(Bucket=self._bucket, Key=key)
        except botocore.exceptions.ClientError as exc:
            # 404 / NoSuchKey -> treat as "not found"
            if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") in (
                404,
            ) or "NoSuchKey" in str(exc):
                raise NotFoundError("Object not found.", code="object_missing")
            raise
        return obj["Body"].read()

    def save_dicom_files(self, study_id: int, files: list[tuple[str, bytes]]) -> None:
        for fname, data in files:
            safe = os.path.basename(fname) or "unnamed.dcm"
            self._put(self._key("studies", study_id, "dicom", safe), data)

    def save_volume(self, study_id: int, buf: bytes, filename: str = "volume.npz") -> str:
        return self._put(self._key("studies", study_id, "volume", filename), buf)

    def load_volume(self, study_id: int):
        raw = self._get_bytes(self._key("studies", study_id, "volume", "volume.npz"))
        import io

        return np.load(io.BytesIO(raw), allow_pickle=False)

    def save_model_mesh(self, study_id: int, vertices: np.ndarray, faces: np.ndarray) -> str:
        # Reuse the same filename scheme as local; but we can't cheaply count
        # existing objects here, so derive a unique key from a timestamp-based
        # counter is avoided — instead embed a stable name and rely on the DB id.
        # For simplicity we write to a deterministically named file keyed by a
        # UUID so concurrent jobs do not collide.
        import uuid

        buf = self._encode_mesh(vertices, faces)
        key = self._key("studies", study_id, "models", f"{uuid.uuid4().hex}.npz")
        return self._put(key, buf)

    def load_model_mesh(self, mesh_path: str):
        import io

        raw = self._get_bytes(mesh_path)
        loaded = np.load(io.BytesIO(raw), allow_pickle=False)
        return loaded["vertices"], loaded["faces"]

    def save_segmentation_mask(self, study_id: int, mask: np.ndarray) -> str:
        import uuid

        buf = _io_bytes(mask)
        key = self._key(
            "studies", study_id, "segmentations", f"{uuid.uuid4().hex}.npz"
        )
        return self._put(key, buf)

    def load_segmentation_mask(self, mask_path: str):
        import io

        raw = self._get_bytes(mask_path)
        return np.load(io.BytesIO(raw), allow_pickle=False)["mask"]

    @staticmethod
    def _encode_mesh(vertices: np.ndarray, faces: np.ndarray) -> bytes:
        import io

        buf = io.BytesIO()
        np.savez_compressed(buf, vertices=vertices, faces=faces)
        return buf.getvalue()


def _io_bytes(array: np.ndarray) -> bytes:
    import io

    buf = io.BytesIO()
    np.savez_compressed(buf, mask=array)
    return buf.getvalue()


def _build_storage():
    backend = (settings.storage_backend or "local").lower()
    if backend == "s3":
        return _S3Storage()
    return _LocalStorage()


# The single storage instance the whole app uses.
storage_service = _build_storage()
