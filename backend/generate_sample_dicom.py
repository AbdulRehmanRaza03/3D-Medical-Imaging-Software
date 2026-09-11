"""Generate sample de-identified CT DICOM files for local testing.

Creates a synthetic-but-valid CT series with a bone-like structure (a ring /
hollow cylinder shape that varies across slices, mimicking a long bone) so the
reconstructed 3D surface actually looks anatomical.

Run:
    cd backend
    py generate_sample_dicom.py
    # writes .dcm files into backend/sample_dicom/
"""
from __future__ import annotations

import io
import os
import uuid

import numpy as np
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

ROWS = 192
COLS = 192
NUM_SLICES = 64
PIXEL_SPACING = 0.98  # mm (typical CT)
SLICE_THICKNESS = 1.5  # mm (typical, creates realistic anisotropy)
RESCALE_INTERCEPT = -1024.0
RESCALE_SLOPE = 1.0


def make_slice_pixels(z_index: int) -> np.ndarray:
    """Create a bone-like cross section at axial position z (in slice units).

    A hollow ring (cortical bone shell) with a small dense core, whose radius
    varies slowly with z so the 3D result looks like a long bone fragment.
    """
    y, x = np.mgrid[0:ROWS, 0:COLS].astype(np.float32)
    cx = COLS / 2.0
    cy = ROWS / 2.0

    # Normalize z to [-1, 1] across the series.
    z = (z_index - (NUM_SLICES - 1) / 2.0) / ((NUM_SLICES - 1) / 2.0)

    # Outer radius of cortical shell (mm), tapering slightly.
    outer_radius = (COLS * 0.30) * (1.0 - 0.1 * abs(z))
    # Cortical thickness.
    thickness = max(6.0, outer_radius * 0.3)

    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    # Bone ring: dense cortical shell.
    ring = (dist <= outer_radius) & (dist >= outer_radius - thickness)

    # Small dense trabecular core in the center.
    core = dist <= outer_radius * 0.35

    # HU values: cortical bone ~ +700, trabecular ~ +300, soft/air ~ -800.
    hu = np.full((ROWS, COLS), -800.0, dtype=np.float32)
    hu[core] = 350.0 + 40.0 * np.sin(z_index / 4.0)
    hu[ring] = 700.0 + 30.0 * np.sin(z_index / 3.0)

    # Add small noise for realism.
    rng = np.random.default_rng(z_index)
    hu += rng.normal(0, 15.0, size=(ROWS, COLS)).astype(np.float32)

    # Convert HU -> stored value.
    stored = (hu - RESCALE_INTERCEPT) / RESCALE_SLOPE
    stored = np.clip(stored, 0, 65535).astype(np.uint16)
    return stored


def build_dataset(z_index: int, series_uid: str, study_uid: str) -> FileDataset:
    """Build one CT image DICOM dataset for slice ``z_index``."""
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)

    ds.PatientID = "ANON-0001"  # de-identified
    ds.PatientName = "ANONYMOUS"
    ds.PatientBirthDate = ""
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.Modality = "CT"
    ds.Rows = ROWS
    ds.Columns = COLS
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.RescaleSlope = RESCALE_SLOPE
    ds.RescaleIntercept = RESCALE_INTERCEPT
    ds.PixelSpacing = [PIXEL_SPACING, PIXEL_SPACING]
    ds.SliceThickness = SLICE_THICKNESS
    ds.InstanceNumber = z_index + 1
    ds.SeriesNumber = 1
    ds.SeriesDescription = "Sample Bone CT (synthetic)"
    ds.StudyDate = "20240101"
    ds.StudyDescription = "OrthoVision sample test study"
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    ds.ImagePositionPatient = [0.0, 0.0, z_index * SLICE_THICKNESS]
    ds.KVP = "120"
    ds.WindowCenter = 400.0
    ds.WindowWidth = 1800.0

    ds.PixelData = make_slice_pixels(z_index).tobytes()

    return ds


def main() -> None:
    out_dir = os.path.join(os.path.dirname(__file__), "sample_dicom")
    os.makedirs(out_dir, exist_ok=True)

    study_uid = generate_uid()
    series_uid = generate_uid()

    written = 0
    for z in range(NUM_SLICES):
        ds = build_dataset(z, series_uid, study_uid)
        fname = f"CT_{z + 1:03d}.dcm"
        path = os.path.join(out_dir, fname)
        ds.save_as(path, enforce_file_format=False)
        written += 1

    print(f"Generated {written} sample CT DICOM files in:")
    print(f"   {out_dir}")
    print(f"\nStudy UID:  {study_uid}")
    print(f"Series UID: {series_uid}")
    print(f"Dimensions: {COLS} x {ROWS} x {NUM_SLICES}")
    print(f"Spacing:    {PIXEL_SPACING} x {PIXEL_SPACING} x {SLICE_THICKNESS} mm")
    print("\n>> Upload ALL these .dcm files together in the frontend.")


if __name__ == "__main__":
    main()
