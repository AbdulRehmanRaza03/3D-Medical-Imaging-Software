"""Tests for DICOM ingestion: validation, series detection, slice ordering."""
from __future__ import annotations

import io

import numpy as np
import pydicom
import pytest

from app.core.exceptions import InvalidDicomError, NoCompatibleSeriesError
from app.services import dicom_service
from tests.conftest import make_ct_dataset, make_ct_series_bytes


def test_detect_series_returns_ct_series():
    files, series_uid = make_ct_series_bytes(num_slices=6)
    datasets = [pydicom.dcmread(io.BytesIO(data)) for _, data in files]
    result = dicom_service.detect_series(datasets)

    assert result.series
    series = result.series[0]
    assert series.series_uid == series_uid
    assert series.modality == "CT"
    assert series.slice_count == 6


def test_slices_sorted_by_spatial_position():
    files, _ = make_ct_series_bytes(num_slices=10)
    datasets = [pydicom.dcmread(io.BytesIO(data)) for _, data in files]
    result = dicom_service.detect_series(datasets)
    series = result.series[0]

    sort_keys = [s.sort_key for s in series.slices]
    assert sort_keys == sorted(sort_keys)
    # Positions should be ascending.
    assert all(k >= 0 for k in sort_keys)


def test_no_ct_series_raises():
    # A non-CT (MR) dataset.
    ds = make_ct_dataset(series_uid="x", instance_number=1, z_position=0.0)
    ds.Modality = "MR"
    buf = io.BytesIO()
    ds.save_as(buf, enforce_file_format=False)
    with pytest.raises(NoCompatibleSeriesError):
        dicom_service.detect_series([pydicom.dcmread(io.BytesIO(buf.getvalue()))])


def test_invalid_bytes_raises():
    with pytest.raises(InvalidDicomError):
        dicom_service.read_dicom_bytes(b"not a dicom file at all")


def test_duplicate_slice_warning():
    files, _ = make_ct_series_bytes(num_slices=4)
    datasets = [pydicom.dcmread(io.BytesIO(data)) for _, data in files]
    # Duplicate the first slice.
    datasets.append(datasets[0])
    result = dicom_service.detect_series(datasets)
    series = result.series[0]
    warnings = " ".join(series.warnings)
    assert "duplicated" in warnings.lower()


def test_hounsfield_rescale():
    from app.services import volume_service

    ds = make_ct_dataset(series_uid="x", instance_number=1, z_position=0.0)
    ds.RescaleSlope = 1.0
    ds.RescaleIntercept = -1024.0
    px = ds.pixel_array
    hu = volume_service.apply_rescale(px, 1.0, -1024.0)
    assert hu.dtype == np.float32
    assert hu.min() >= -1024.0
