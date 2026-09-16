"""Storage layer for OrthoVision AI.

Exposes a single ``storage_service`` instance that abstracts where binary
medical artifacts (DICOM files, volumes, meshes, segmentation masks) are
persisted.

Supported backends:

- ``local`` (default): plain filesystem under ``STORAGE_DIR``.
- ``s3``: any S3-compatible object store (Supabase Storage, Cloudflare R2,
  AWS S3, MinIO) configured via ``STORAGE_BACKEND=s3`` plus the standard
  ``AWS_*`` / ``S3_*`` environment variables.

The interface is deliberately small and stable so the rest of the application
never depends on *where* files live.
"""

from app.services.storage.storage_service import storage_service

__all__ = ["storage_service"]
