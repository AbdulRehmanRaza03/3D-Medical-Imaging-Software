# API Reference

Base URL: `http://localhost:8000` · Base path: `/api/v1`

Errors use a consistent shape:

```json
{ "detail": "Human-readable message", "code": "machine_code" }
```

## Health

### `GET /health`

```json
{ "status": "ok", "app": "OrthoVision AI" }
```

## Studies

### `POST /studies/upload`

Multipart form: one or more `files` (DICOM), optional `name`.

Response (201):

```json
{
  "study": { "id": 1, "modality": "CT", "slice_count": 164, ... },
  "series_detected": 1,
  "warnings": []
}
```

Errors: `422 invalid_dicom`, `422 no_compatible_series`.

### `GET /studies`

```json
{ "studies": [ ... ], "total": 1 }
```

### `GET /studies/{id}`

Study detail including `series` array.

### `GET /studies/{id}/series`

List of series for the study.

### `GET /studies/{id}/metadata`

Extracted study/series metadata (spacing, dimensions, orientation, …).

## Slices

### `GET /studies/{id}/slice/{index}`

Optional query params `width`, `level` (window/level). Returns a windowed 8-bit
PNG slice:

```json
{
  "index": 82, "total": 164,
  "width": 400, "level": 40,
  "rows": 512, "columns": 512,
  "image_base64": "..."
}
```

## Reconstruction & Models

### `POST /studies/{id}/reconstruct`

```json
{
  "threshold_hu": 300,
  "remove_small_components": true,
  "method": "marching_cubes"
}
```

Returns `{ "job_id": "..." }`.

### `GET /studies/{id}/models`

```json
{ "models": [ { "id": 1, "vertices": 124520, "triangles": 249018, ... } ] }
```

### `GET /models/{id}/mesh`

Binary GLB of the model (for the 3D viewer).

## Measurements

### `POST /models/{id}/measurements`

```json
{ "points": [[0,0,0],[10,0,0]], "measurement_type": "distance" }
```

Returns the computed measurement (`value`, `unit`).

## Export

### `GET /models/{id}/export/{stl|obj|glb}`

Download the actual mesh file.

## Jobs

### `GET /jobs/{id}`

```json
{
  "id": "...", "status": "processing", "progress": 0.75,
  "message": "Thresholding…", "result_model_id": null
}
```

Statuses: `queued`, `processing`, `completed`, `failed`.
