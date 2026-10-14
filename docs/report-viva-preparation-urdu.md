# OrthoVision AI — Viva Preparation Report (Roman Urdu)

> Yeh report **viva / interview / presentation** ki tayyari ke liye hai. Is mein project ko **A se Z** — har concept, har decision, har technical cheez — examples ke saath samjhaya gaya hai. Isay parh kar aap kisi bhi sawaal ka confident jawab de sakte ho.

---

## 1. Project Ka Introduction (Aap Se Pehla Sawaal Yehi Hoga)

**"Apna project batao?"**

Jawab ka structure:

> OrthoVision AI ek **medical 3D imaging platform** hai jo CT DICOM scans ko browser mein **interactive 3D models** mein convert karta hai. Iska core purpose hai de-identified CT data se **anatomically accurate 3D bone surface** banana, jise doctor/researcher ghooma saken, clip kar saken, naap saken (mm mein), aur STL/OBJ/GLB mein export kar saken.

**Ek line mein:** "2D CT scan → 3D rotatable model."

---

## 2. Problem Statement (Kyun Banaya)

- CT/MRI data **2D slices** mein aata hai, doctor ko 3D samajhna mushkil hota hai.
- 3D visualization **medical research, education, aur future surgical planning** ke liye valuable hai.
- Existing tools mahngi/closed-source hoti hain. Ye project ek **open, web-based, research-grade** core foundation banata hai.

---

## 3. Medical Imaging Ke Core Concepts (Ye Aapko Rate Zroor Puchenge)

### 3.1 DICOM Kya Hai?

**DICOM (Digital Imaging and COmmunications in Medicine)** ek standard format hai medical images ke liye. Har file mein:
1. **Pixel data** (actual image)
2. **Metadata** (patient info, scanner settings, spacing, orientation)

**Example:** `CT_001.dcm` = 512×512 image + PixelSpacing=0.68mm + ImagePositionPatient + ImageOrientationPatient.

### 3.2 Hounsfield Unit (HU)

CT mein har pixel ki value HU mein hoti hai, jo tissue density batati hai:

| Material | HU |
|----------|-----|
| Air | -1000 |
| Water | 0 |
| Soft tissue | +40 ~ +100 |
| Bone | +300 ~ +3000 |

**Formula:** `HU = PixelValue × RescaleSlope + RescaleIntercept`

Ye project mein `apply_rescale()` karta hai (`volume_service.py`).

### 3.3 Voxel vs Pixel

- **Pixel** = 2D image ka chota box
- **Voxel** = 3D volume ka chota box (volume-pixel)

CT slices stack karne se 3D voxel grid banti hai.

### 3.4 Spatial/Anisotropic Spacing (Sabse Important Medical Concept)

CT mein:
- **Pixel spacing (x,y)** = chhota (e.g. 0.5mm)
- **Slice thickness (z)** = bada (e.g. 2mm)

Matlab voxel **cube nahi, box** hai. Agar hum ye ignore karein, to 3D model **dab jayega (squashed)**.

**Fix jo project ne kiya:** Marching Cubes ke baad har vertex ko `<spacing>` se multiply karte hain. Ye `marching_cubes_mesh()` mein hai.

> **Viva mein bolna:** "Spatial correctness paramount hai — bina spacing scaling ke model anatomically galat hoga."

### 3.5 Image Orientation / Position

- `ImagePositionPatient` = slice ki 3D position (mm)
- `ImageOrientationPatient` = slice ka direction

Inse hum **slice ko sahi order** mein lagate hain (filename se nahi).

---

## 4. Full Pipeline (Step-by-Step — Iska Flow Diagram Rat Lo)

```
1. Upload DICOM files
2. Validate (dicom_service.validate_dicom_dataset)
3. Detect series (group by SeriesInstanceUID)
4. Order slices (spatial, compute_slice_sort_key)
5. Build volume (HU, volume_service.build_volume)
6. Threshold → binary mask (bone >= 300 HU)
7. Marching Cubes → mesh surface
8. Scale by spacing → anatomical mesh
9. Export GLB → frontend 3D viewer
```

Har step ka **file reference** rat lo:
- `dicom_service.py` → validation, series, ordering
- `volume_service.py` → HU + volume
- `reconstruction_service.py` → threshold + Marching Cubes
- `mpr_service.py` → MPR planes
- `coordinate_service.py` → voxel↔world
- `export_service.py` → STL/OBJ/GLB

---

## 5. Marching Cubes (Alag Se Rate Karna — Ye Important Algorithm Hai)

**Question:** "3D surface kaise banta hai?"

**Jawab:**
> Marching Cubes ek classic algorithm hai jo binary voxel grid se **triangle mesh** nikalta hai. Ye har 8-voxel cube (cell) ko dekhta hai, aur surface ke intersections ki triangles banata hai. Output = vertices + faces (triangles).

**Project specifics:**
- `skimage.measure.marching_cubes()` use karta hai
- Level = 0.5 (binary mask threshold)
- Padding 1 voxel (boundary truncation avoid karne ke liye)
- **Scaling:** verts × spacing (anisotropic correction)
- Cleanup: degenerate faces remove, unused vertices drop, optional Laplacian smoothing (conservative, anatomy preserve)

---

## 6. Coordinate System (Voxel ↔ World)

**Question:** "Measurement mm mein kaise aati hai?"

**Jawab:**
> Hum `CoordinateSystem` banate hain jo spacing, origin aur direction (3×3 rotation) se affine transform banata hai. Ye voxel index ko physical world (mm) mein convert karta hai.

**Formula:**
```
world = origin + direction @ (index × spacing)
```

Isi se distance (mm) aur angle (°) sahi aate hain, screen pixels se nahi.

**File:** `coordinate_service.py` — `voxel_to_world()` aur `world_to_voxel()`.

---

## 7. MPR (Multiplanar Reconstruction)

**Question:** "MPR kya hai?"

**Jawab:**
> Ek 3D volume se 3 orthogonal 2D planes nikaalna:
> - **Axial** = z slice (upar se)
> - **Coronal** = y slice (aage se)
> - **Sagittal** = x slice (side se)

Ye **same volume ka re-slice** hai, koi interpolation ya duplicate copy nahi. Crosshair 3 planes ko sync karta hai.

**File:** `mpr_service.py` + `MPRWorkspace.tsx` (frontend).

---

## 8. Architecture Design (High-Level)

```
Frontend (Next.js/React/Three.js) ↔ REST+GLB API ↔ Backend (FastAPI/Python)
Backend → SQLite/PostgreSQL (metadata) + File/Storage (binary)
```

**4 Design Principles (Viva Mein Bolna):**
1. **Medical logic isolated** — services pure Python, independently testable
2. **3D rendering decoupled** — binary GLB transport, DICOM se alag
3. **Spatial correctness** — spacing/origin/direction preserve
4. **AI-ready boundaries** — segmentation future mein `MeshData` shape emit kare

---

## 9. Tech Stack (Poochha Jayega)

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind, TanStack Query, Three.js, React Three Fiber, Drei |
| Backend | Python 3.14, FastAPI, Pydantic v2, Uvicorn, SQLAlchemy 2 |
| Medical | pydicom, NumPy, SciPy, scikit-image (Marching Cubes) |
| AI | PyTorch, MONAI (3D U-Net — optional) |
| Mesh | trimesh (STL/OBJ/GLB) |
| DB | SQLite → PostgreSQL |
| Test | pytest (backend), Vitest (frontend) |
| Deploy | Vercel (frontend), Render/Fly (backend), Supabase/R2/Redis |

---

## 10. AI Segmentation (Phase 3 — Honest Status)

**Question:** "AI kahan hai?"

**Jawab (honest, yehi sahi hai):**
> AI segmentation ki **poori architecture implement hai** — MONAI 3D U-Net, model registry, preprocessing (HU clip + normalize), inference, postprocessing (threshold + largest component), metrics (Dice/IoU). **Lekin trained model (checkpoint) abhi provide nahi hui**, isliye inference run nahi hoti. System honestly "checkpoint required" bolta hai — fake result nahi deta.

**Ye honesty research/PhD interviewer ko impress karti hai.**

**Pipeline:**
```
volume → preprocessing (HU clip → normalize → tensor) → 3D U-Net → softmax → postprocessing → mask → labels (volume, bbox, centroid)
```

**Files:** `ai/segmentation/*` (registry, model, inference, preprocessing, postprocessing, metrics, service, config, schemas).

---

## 11. Background Jobs (Async Processing)

**Question:** "Long reconstruction kaise handle hoti hai?"

**Jawab:**
> Reconstruction CPU-heavy hai, isliye background job system hai. Job DB mein persist hoti hai (queued → processing → completed/failed), frontend poll karta hai.

**Do backends:**
- `local` → in-process threads (dev)
- `redis` → RQ queue + worker (production)

**File:** `job_service.py` + `worker.py`.

---

## 12. Storage

**Question:** "Data kahan store hota?"

**Jawab:** Do jagah:
1. **Metadata** → database (SQLite/Postgres)
2. **Binary** (DICOM, volume .npz, mesh .npz) → storage (local filesystem ya S3-compatible)

**File:** `storage/storage_service.py` — pluggable (`local` ya `s3`).

---

## 13. Testing (Poochega — Kitna Test Hua)

> "56 backend tests + 19 frontend tests, sab pass. Typecheck bhi clean."

**Backend tests cover:** DICOM validation, series detection, spatial ordering, HU conversion, volume, MPR, coordinates, reconstruction, Marching Cubes (anisotropic spacing), mesh cleanup, export, measurements, segmentation infra, API responses.

**Frontend tests cover:** StudyList, ModelInfo, WindowLevelControls, viewer-store, API client, useSegmentation.

---

## 14. Deployment

**Stack:** Vercel (frontend) + Render (backend) + Supabase/Postgres + Redis + S3-compatible storage.

**Files:** `Dockerfile`, `Dockerfile.worker`, `render.yaml`, `fly.toml`, `vercel.json`, `.env.example`.

---

## 15. Challenges & Learnings (Interviewer Ye Puchenge)

1. **SimpleITK → custom pipeline** — Windows DLL incompatibility ki wajah se SimpleITK drop kiya, direct pydicom+NumPy+SciPy+scikit-image use kiya. Same correctness, full control.

2. **psycopg2 Python 3.14 issue** — wheel nahi tha, `psycopg3` pe switch kiya.

3. **Ephemeral disk production issue** — Render free pe data gayab hota, persistent storage chahiye.

4. **CORS double-slash bug** — trailing slash URL se `//api/v1` ban raha tha.

5. **AI without checkpoint** — honest gating ka design decision.

---

## 16. Honest Limitations (Yeh Bolna Zaroori Hai — Credibility)

1. AI **architecture complete**, inference **pending trained model**
2. Production **persistence** demo mode pe (local storage), real cloud storage pending
3. **Real DICOM** end-to-end verify abhi pending (synthetic data pe tested)
4. **No authentication** (research/demo scope)
5. **No segmentation 3D overlay** abhi

> Ye kehne se interviewer ko pata chalta hai ke tumhe **project ki limit ka honest pata hai** — ye PhD/20-saal expert ke saamne sabse bara plus point hai.

---

## 17. Future Work (Roadmap)

| Phase | Kya |
|-------|-----|
| 4 | Intelligent analysis (volume, symmetry, ICP registration, deviation maps) |
| 5 | Orthopaedic planning (implant) |
| 6 | Research platform (projects, annotations, collaboration, reports) |
| 7 | AI assistant (natural language querying) |

---

## 18. 10 Most Likely Viva Questions + Answers

1. **Q: Medical correctness kaise ensure hui?**
   A: Spatial ordering, HU conversion, anisotropic spacing scaling, coordinate affine — sab tested.

2. **Q: 3D model 2D se kaise banta?**
   A: Volume → threshold → Marching Cubes → spacing-scaled mesh.

3. **Q: Measurement mm mein kyun?**
   A: Coordinate system se voxel→world conversion.

4. **Q: MPR kya hai?**
   A: Same volume ka 3 orthogonal planes mein re-slice.

5. **Q: AI working hai?**
   A: Architecture hai, checkpoint nahi, honest gating.

6. **Q: Background jobs?**
   A: DB-persisted jobs + polling, local threads ya Redis/RQ.

7. **Q: Storage?**
   A: Metadata DB mein, binary files local/S3 mein.

8. **Q: Kitna test?**
   A: 56 backend + 19 frontend, sab pass.

9. **Q: Tech stack?**
   A: FastAPI + Next.js + Three.js + PyTorch/MONAI.

10. **Q: Aage kya?**
    A: Persistent production, AI checkpoint, Phases 4+.

---

## 19. Summary Checklist (Presentation Se Pehle)

- [x] Problem statement
- [x] Medical concepts (DICOM, HU, voxel, spacing)
- [x] Pipeline flow
- [x] Marching Cubes
- [x] Coordinate system
- [x] MPR
- [x] Architecture design
- [x] AI status (honest)
- [x] Testing results
- [x] Challenges & limitations
- [x] Future roadmap

**Key message (yaad rakho):** "Solid Phase 1-2 engineering, honest AI architecture, tested pipeline, clear roadmap."
