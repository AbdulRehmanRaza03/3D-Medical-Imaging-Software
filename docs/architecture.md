# Architecture

## Overview

OrthoVision AI is split into two deployable components communicating over a
typed REST API:

- **Frontend** — Next.js SPA (App Router) rendering the dashboard, study
  browser, and the medical viewer (2D + 3D).
- **Backend** — FastAPI application exposing a clean service-oriented medical
  imaging pipeline.

```
┌───────────────────────────────────────────────────────────┐
│ Frontend (Next.js + React + Three.js)                     │
│                                                           │
│  Dashboard  Study Browser  Medical Viewer                 │
│    │             │             │                          │
│    │      ┌──────┴──────┐  ┌───┴────────────┐             │
│    │      │ DicomUploader│  │ SliceViewer    │             │
│    │      │ StudyList   │  │ ThreeDViewer   │             │
│    │      └─────────────┘  │ Controls       │             │
│    │                       └────────────────┘             │
│    └─────────────── TanStack Query (api client) ──────────┤
└───────────────────────────────┬───────────────────────────┘
                                │ REST / JSON + binary GLB
┌───────────────────────────────▼───────────────────────────┐
│ FastAPI backend                                            │
│                                                           │
│  API routers (studies, slices, models, jobs)              │
│     │                                                     │
│  Services                                                 │
│  ├── dicom_service       (validation / series / ordering) │
│  ├── study_service       (orchestration)                  │
│  ├── volume_service      (HU + 3D volume)                 │
│  ├── reconstruction_service (mask + marching cubes)       │
│  ├── measurement_service (distance / angle)               │
│  ├── export_service      (STL / OBJ / GLB)                │
│  ├── job_service         (background processing)          │
│  └── storage_service     (structured file storage)        │
│     │                                                     │
│  SQLAlchemy models (Study, Series, MeshModel, Job, ...)   │
│  └── SQLite (default) / PostgreSQL (prod)                 │
└───────────────────────────────────────────────────────────┘
```

## Key design decisions

1. **Medical logic separated from web/HTTP.** Every service operates on plain
   Python data (`pydicom.Dataset`, `SeriesInfo`, `Volume`, `MeshData`) and can
   be unit-tested without a server.

2. **Spatial correctness.** Volumes carry `spacing`, `origin`, and `direction`.
   Marching Cubes output is scaled by voxel spacing so the mesh is physically
   accurate, not distorted by anisotropic CT voxels.

3. **Binary transport for meshes.** Large meshes are served as binary GLB rather
   than JSON to avoid massive serialization overhead; STL/OBJ/GLB exports write
   the actual mesh to disk on demand.

4. **Jobs decoupled from the transport.** The job service uses a thread pool but
   exposes a job-ID + poll contract, so Redis/Celery can replace it later.

5. **AI-ready boundaries.** A future `ai_segmentation_service` can slot in
   alongside `reconstruction_service` and output the same `MeshData` shape.

## Directory layout

```
backend/
  app/
    api/              # FastAPI routers
    core/             # config, exceptions, logging
    db/               # SQLAlchemy engine/session
    models/           # ORM models
    schemas/          # Pydantic request/response contracts
    services/         # medical pipeline services
      storage/        # filesystem storage helpers
  tests/              # pytest suite + fixtures
frontend/
  src/
    app/              # Next.js pages (dashboard, upload, study/[id])
    components/
      medical/        # viewer + domain components
    hooks/            # TanStack Query hooks
    lib/api/          # typed API client
    types/            # shared TypeScript types
```
