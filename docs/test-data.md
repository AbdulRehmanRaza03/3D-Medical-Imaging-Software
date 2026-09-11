# Test Data

OrthoVision AI requires **real de-identified CT DICOM data** to exercise the
full pipeline. Large medical datasets are **not committed to this repository**.

## Obtaining a legal public dataset

Use a public, de-identified, license-permitting CT dataset. Recommended sources:

- **The Cancer Imaging Archive (TCIA)** — https://www.cancerimagingarchive.net/
  - Offers many public CT collections. Requires an account; some collections
    require a data-access agreement.
- **Visible Human Project (NLM)** — https://www.nlm.nih.gov/research/visible/
- **MedPix** (NLM) — https://medpix.nlm.nih.gov/
- **OsiriX DICOM sample images** — https://www.osirix-viewer.com/resources/dicom-image-library/
  - Small, publicly downloadable anonymized DICOM datasets (good for quick
    testing).

> Always verify the license/usage terms of the specific dataset before using it.

## Expected folder structure

A typical unzipped CT study looks like:

```
my_study/
  ├── IM-0001-0001.dcm
  ├── IM-0001-0002.dcm
  ├── ...
  └── IM-0001-0164.dcm
```

Individual `.dcm` files (each one a slice of the CT series) are all you need.

## Uploading

1. Start the backend and frontend (see README).
2. Go to **Quick Upload**.
3. Drag-and-drop (or select) all the `.dcm` files of a single series.
4. Wait for ingestion (`ready` status).

Multiple series can be uploaded together; the backend groups by
`SeriesInstanceUID` and selects the first CT series as primary.

## What the application should produce

- A study entry with the correct modality (`CT`), slice count, and metadata.
- An axial 2D viewer you can scroll through.
- A bone surface (3D model) after reconstruction, with physical dimensions
  matching the DICOM spacing.
- Exportable STL/OBJ/GLB files containing the actual reconstructed mesh.

## Repository fixtures (for automated tests only)

The backend test suite uses a **synthetic-but-valid CT DICOM generator**
(`backend/tests/conftest.py`) built with pydicom. These files are valid DICOM
datasets with correct orientation/position tags and pixel data — used only to
exercise the pipeline in tests, never shipped as "patient data" or used as the
primary validation dataset. For real accuracy work, use a real de-identified
dataset as described above.
