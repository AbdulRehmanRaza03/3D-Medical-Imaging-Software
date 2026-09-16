# Real Medical Data & Storage Backends

This guide explains how to obtain **real de-identified CT DICOM data** and how
to wire **Supabase** (recommended) or **Firebase** for the database and storage
layers in production.

> ⚠️ OrthoVision AI is a research/visualization platform, **not** a diagnostic
> device. Always use legally obtained, de-identified data with proper
> consent/licensing. Never ingest PHI (Protected Health Information).

---

## 1. Obtaining Real De-identified CT DICOM Data

| Source | What it provides | License / Access |
| ------ | ---------------- | ---------------- |
| **The Cancer Imaging Archive (TCIA)** | Large public collection of CT/MRI DICOM studies | Free; some require agreement |
| **Medical Segmentation Decathlon** | 3D CT volumes + segmentation labels (great for training) | Free research license |
| **OpenNeuro** | Brain imaging datasets | Free (CC / dataset-specific) |
| **COVID-19 CT datasets** (e.g. MosMedData) | Chest CT studies | Free research |
| **TotalSegmentator dataset** | Full-body CT + 104 anatomical labels | Free (research) |
| **Grand Challenge** | Multiple medical imaging challenges | Varies |

**Recommended starting points for a bone/orthopaedic demo:**

- **TotalSegmentator** (full-body CT with bone labels) — ideal for testing the
  Marching Cubes bone reconstruction.
- **Medical Segmentation Decathlon** (Task 01–10) — labeled CT for training the
  3D U-Net AI model.

### How to load them

1. Download a CT study (a folder of `.dcm` files, or a `.nii/.nii.gz` that
   you convert to DICOM).
2. Upload the `.dcm` files through the frontend, or use the backend directly:
   ```bash
   # Convert NIfTI -> DICOM (if needed) using a tool like plastimatch or dcm2niix in reverse
   ```
3. Reconstruct with a **300 HU** threshold (default) to isolate bone.

---

## 2. Database + Storage: Supabase (Recommended)

**Why Supabase over Firebase for this project?**
- OrthoVision AI already uses **PostgreSQL / SQLAlchemy** on the backend.
  Supabase *is* PostgreSQL + S3-compatible storage + auth in one place — no
  rearchitecting.
- Firebase (Firestore) is a NoSQL document store; migrating the existing
  relational schema (studies, series, models, jobs, segmentations) would be a
  large rewrite and is unnecessary here.

### Supabase wiring

1. Create a project at https://supabase.com.
2. **Database connection string** (for `DATABASE_URL`):
   - Project Settings → Database → Connection string.
   - Use the **Session pooler** URI (port `5432` with `?pgbouncer=true`) for
     serverless/HTTP backends, or the **Direct** connection for a long-lived
     backend (Render/Fly persistent services).
3. **Storage (for binary DICOM/volume/mesh artifacts)**:
   - Project Settings → Storage → enable S3 API.
   - Copy the **S3 Access Key / Secret Key / Endpoint / Region** into the
     backend env vars (`STORAGE_BACKEND=s3`).

---

## 3. Firebase (Alternative / Optional)

Firebase is **not required** and is **not recommended** as the primary database
for this codebase. If you want Firebase only for **authentication** (user
accounts for a research portal, Phase 6+), you can add it alongside Supabase:

- Use **Firebase Auth** for sign-in (Google/GitHub/email).
- Keep **Supabase PostgreSQL** for metadata and **Supabase/R2** for storage.

Firestore/Firebase Storage would only make sense if you replace the entire
backend persistence layer, which is out of scope for this architecture.

---

## 4. Putting It Together (Production `.env`)

```text
# Database — Supabase PostgreSQL
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres?sslmode=require

# Storage — S3-compatible (Supabase Storage or Cloudflare R2)
STORAGE_BACKEND=s3
S3_BUCKET_NAME=your-bucket
S3_ENDPOINT_URL=https://YOUR_PROJECT.supabase.co/storage/v1/s3
S3_REGION=us-east-1
S3_ACCESS_KEY=YOUR_S3_ACCESS_KEY
S3_SECRET_KEY=YOUR_S3_SECRET_KEY

# Job queue — Redis
JOB_BACKEND=redis
REDIS_URL=redis://default:YOUR_PASSWORD@YOUR_HOST:6379/0
REDIS_QUEUE=orthovision

# Frontend origin
CORS_ORIGINS=https://your-app.vercel.app

# AI (optional) — set if running the GPU/AI worker
# OV_MODELS_DIR=/app/ai/segmentation/models
```

---

## 5. Deploying with AI + Redis (full architecture)

```mermaid
graph TD
    F[Vercel Frontend] --> B[Render Web - FastAPI]
    B --> W[Render Worker - RQ]
    W --> R[(Redis)]
    W --> G[GPU worker - AI segmentation]
    B --> D[(Supabase PostgreSQL)]
    B --> S[(S3 / R2 storage)]
    G --> S
```

1. **Web service** (FastAPI) — serves API, enqueues jobs.
2. **Worker (CPU)** — runs reconstruction jobs from Redis.
3. **Worker (GPU, optional)** — runs AI segmentation (`torch` + `monai`),
   consuming the same Redis queue.
4. **Redis** — job queue.
5. **Supabase PostgreSQL** — metadata.
6. **S3/R2** — binary artifacts.
