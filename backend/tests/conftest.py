"""Shared pytest fixtures, including a synthetic-but-valid CT DICOM generator.

The generated DICOM files are *real* DICOM datasets (valid tag structure,
PixelData, correct orientation/position tags) created with pydicom. They are
minimal synthetic CT data used only to exercise the pipeline in tests — never
shipped as "patient data".
"""
from __future__ import annotations

import io
import uuid

import numpy as np
import pydicom
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid


@pytest.fixture(autouse=True)
def _isolated_test_environment(monkeypatch):
    """Force safe local defaults during tests.

    The developer's ``.env`` may point at production services (S3 storage,
    PostgreSQL, Redis). Tests must never touch those, so we override the
    network-dependent backends with local equivalents before any module
    imports the app or storage layer.
    """
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("JOB_BACKEND", "local")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_orthovision.db")
    # Re-import settings so the overrides take effect before ``app`` is built.
    import app.core.config as config

    config.get_settings.cache_clear()
    config.settings = config.get_settings()


def make_ct_dataset(
    *,
    series_uid: str,
    instance_number: int,
    z_position: float,
    rows: int = 16,
    columns: int = 16,
    pixel_spacing: tuple[float, float] = (0.5, 0.5),
    slice_thickness: float = 1.0,
    study_uid: str | None = None,
    patient_id: str = "TEST_ANON",
) -> FileDataset:
    """Create a single valid CT image DICOM dataset.

    Pixel data encodes a small synthetic structure: a bright (bone-like) square
    in the center that varies with ``instance_number`` so the slices differ.
    """
    study_uid = study_uid or generate_uid()

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image Storage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)

    ds.PatientID = patient_id
    ds.PatientName = "ANONYMOUS"
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.Modality = "CT"
    ds.Rows = rows
    ds.Columns = columns
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.RescaleSlope = 1.0
    ds.RescaleIntercept = -1024.0  # typical CT -> HU
    ds.PixelSpacing = list(pixel_spacing)
    ds.SliceThickness = slice_thickness
    ds.InstanceNumber = instance_number
    ds.SeriesNumber = 1
    ds.StudyDate = "20240101"
    ds.SeriesDescription = "Synthetic CT Test Series"

    # Orientation: axial (row = +x, col = +y, normal = +z).
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    ds.ImagePositionPatient = [0.0, 0.0, z_position]

    # Synthetic pixel data: a bright central block + noise floor.
    px = np.full((rows, columns), 0, dtype=np.int16)
    r0, r1 = rows // 4, 3 * rows // 4
    c0, c1 = columns // 4, 3 * columns // 4
    # Bone-like HU (~300+) translated back to stored value.
    stored = int(300.0 - ds.RescaleIntercept)  # = 1324
    # Vary intensity slightly per slice so volume isn't constant.
    px[r0:r1, c0:c1] = stored + (instance_number % 5)
    ds.PixelData = px.tobytes()

    return ds


def make_ct_series_bytes(
    num_slices: int = 8,
    *,
    rows: int = 16,
    columns: int = 16,
    pixel_spacing: tuple[float, float] = (0.5, 0.5),
    slice_thickness: float = 1.0,
) -> tuple[list[tuple[str, bytes]], str]:
    """Generate ``num_slices`` DICOM files for one CT series, unordered.

    Files are intentionally emitted in non-monotonic order to prove that the
    pipeline sorts by spatial position, not filename/insertion order.
    """
    series_uid = generate_uid()
    files: list[tuple[str, bytes]] = []

    # Create slices with z positions and emit in shuffled order.
    positions = list(range(num_slices))
    order = positions[:]
    np.random.default_rng(42).shuffle(order)

    for i in order:
        ds = make_ct_dataset(
            series_uid=series_uid,
            instance_number=i + 1,
            z_position=float(i) * slice_thickness,
            rows=rows,
            columns=columns,
            pixel_spacing=pixel_spacing,
            slice_thickness=slice_thickness,
        )
        buf = io.BytesIO()
        ds.save_as(buf, enforce_file_format=False)
        files.append((f"slice_{i:03d}.dcm", buf.getvalue()))

    return files, series_uid


@pytest.fixture
def ct_series_bytes():
    return make_ct_series_bytes(num_slices=8)
