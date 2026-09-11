# DICOM Pipeline

The DICOM ingestion pipeline transforms raw uploaded files into a spatially
aware 3D CT volume and study metadata.

## Stages

1. **Parse & validate** — Each uploaded file is parsed with `pydicom.dcmread`.
   Required tags are checked (`StudyInstanceUID`, `SeriesInstanceUID`,
   `Modality`, `Rows`, `Columns`, `PixelData`, `ImagePositionPatient`,
   `ImageOrientationPatient`, `PixelSpacing`, …).

2. **Series detection** — Datasets are grouped by `SeriesInstanceUID`. Only
   series with image instances and `Modality == "CT"` are retained.

3. **Slice ordering** — Slices are ordered by projecting `ImagePositionPatient`
   onto the slice normal (the cross product of the `ImageOrientationPatient`
   row/column cosines). This is *spatially* correct and does **not** rely on
   filename order.

4. **Quality warnings** — The pipeline reports duplicate slice positions,
   irregular slice spacing, non-axial orientation, and low slice counts rather
   than silently producing incorrect 3D data.

5. **Metadata extraction** — Patient/study/series identifiers, dimensions,
   pixel spacing, slice thickness, orientation, and reconstruction parameters
   (RescaleSlope/Intercept) are captured. Patient identifiers are **not**
   exposed in API responses.

6. **Volume construction** — Slices are stacked into a `Volume` (see below),
   converted to Hounsfield Units, and persisted to disk.

## Internal data model

```python
Study      # one DICOM study (StudyInstanceUID)
Series     # one CT series within the study
Slice      # a single ordered 2D image instance
Volume     # data + spacing + origin + direction + dimensions
```

## Ordering correctness

The sort key is the signed projection of `ImagePositionPatient` onto the axial
normal:

```
normal = cross(ImageOrientationPatient[0:3],
               ImageOrientationPatient[3:6])
sort_key = dot(ImagePositionPatient, normal)
```

Fallbacks (in order): `ImagePositionPatient[2]`, `InstanceNumber`.

## HU conversion

```
HU = stored_value * RescaleSlope + RescaleIntercept
```

A typical CT uses `RescaleSlope = 1.0`, `RescaleIntercept = -1024.0`.
