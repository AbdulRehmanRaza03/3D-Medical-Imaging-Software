"""Application-specific exceptions mapped to clean HTTP errors."""
from __future__ import annotations


class OrthoVisionError(Exception):
    """Base exception for the application."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class InvalidDicomError(OrthoVisionError):
    status_code = 422
    code = "invalid_dicom"


class NoCompatibleSeriesError(OrthoVisionError):
    status_code = 422
    code = "no_compatible_series"


class NotFoundError(OrthoVisionError):
    status_code = 404
    code = "not_found"


class ProcessingError(OrthoVisionError):
    status_code = 422
    code = "processing_error"


class ValidationError(OrthoVisionError):
    status_code = 400
    code = "validation_error"
