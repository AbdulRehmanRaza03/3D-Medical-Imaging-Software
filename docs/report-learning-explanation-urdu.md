# OrthoVision AI — Learning & Explanation Report (Roman Urdu)

> Yeh report **seekhnay aur sawaalon ke jawab denay** ke liye hai. Is mein project ko step-by-step, examples ke saath, aasaan zubaan mein samjhaya gaya hai. Koi bhi naya banda isay parh ke samajh sakay ke project kaise kaam karta hai.

---

## Kya Hai Yeh Project? (Ek Line Mein)

OrthoVision AI ek software hai jo **hospital ke CT scans (DICOM files)** ko **3D model** mein badal deta hai — jo browser mein ghoomaya, kata (clip), naapa (measure) aur export kiya ja sakta hai.

**Aasaan matlab:** Doctor ko 2D image ki bajaye ek **rotatable 3D haddi (bone)** dikh jaye.

---

## Medical Imaging Ka Basic Cheezein (Pehle Ye Samjho)

### 1. DICOM Kya Hai?

DICOM ek **file format** hai jo medical scanners (CT/MRI) use karte hain. Har file mein:
- Pixel data (image)
- Metadata (patient info, spacing, orientation)

**Example:** `CT_001.dcm` ke andar ek 512x512 image hai + ye batata hai ke pixel ka physical size 0.68mm hai.

### 2. Hounsfield Unit (HU) Kya Hai?

CT scan mein har pixel ki value ek number hoti hai jise **HU** kehte hain. Ye different tissues ko alag karti hai:

| Material | HU Value |
|----------|----------|
| Hawa (air) | -1000 |
| Paani (water) | 0 |
| Soft tissue (flesh) | +40 se +100 |
| Haddi (bone) | +300 se +1000+ |

**Is project ka core idea:** 300 HU se zyada value wale pixels = bone. Isi se bone ka 3D model banaya jata hai.

### 3. Voxel Kya Hai?

2D image mein "pixel" hota hai, 3D volume mein **"voxel"** (volume + pixel). CT slices ko stack karke ek 3D box banta hai jisme har chota dibba (voxel) ek HU value rakhta hai.

---

## Project Kaise Kaam Karta Hai (Step-by-Step)

### Step 1: Upload
User browser mein DICOM files drag-drop karta hai. Backend files receive karta hai.

**Code:** `DicomUploader.tsx` (frontend) → `studies.py` endpoint → `study_service.ingest_study()`.

### Step 2: Validate + Detect Series

Backend har file ko pydicom se parhta hai, check karta hai ke CT hai, aur files ko **series** mein group karta hai.

**Example:** 100 files aayi, sab same `SeriesInstanceUID` ki hain = ek series.

**Code:** `dicom_service.detect_series()`.

### Step 3: Slice Ordering (Sabse Zaroori Medical Logic)

Files galat order mein bhi aa sakti hain. Backend har slice ki **ImagePositionPatient** (sharir mein position) use kar ke unhe **anatomically correct order** mein lagata hai — filename se nahi.

**Code:** `compute_slice_sort_key()` — ye slice normal direction pe project karta hai.

### Step 4: Volume Build (2D → 3D)

Ordered slices ko stack karke ek 3D array banta hai: `(depth, height, width)`. Har value HU mein convert hoti hai.

**Code:** `volume_service.build_volume()`.

### Step 5: Thresholding (Bone Nikalna)

300 HU se zyada value wale voxels = bone (1), baqi = background (0). Ek binary mask banta hai.

**Code:** `reconstruction_service.threshold_mask()`.

### Step 6: Marching Cubes (3D Surface Nikaalna)

Binary mask se ek **mesh** (surface) nikalta hai — ye sirf andar ke cubes nahi, balki **surface ke triangles** hain. Phir har vertex ko physical spacing se multiply karte hain (taake size real anatomy ke equal ho).

**Code:** `marching_cubes_mesh()`.

> ⚠️ **Anisotropic spacing** important hai: agar slice thickness (z) 2mm hai aur pixel (x,y) 0.5mm hai, to bina scaling ke model "dab jayega". Is project ne ye sahi handle kiya hai.

### Step 7: 3D Viewer (Browser Mein Dikhana)

Mesh ko GLB (binary 3D format) mein convert karke browser ke Three.js/R3F viewer ko bheja jata hai. User orbit/zoom/pan kar sakta hai.

**Code:** `export_service.export_glb()` → `ThreeDViewer.tsx`.

---

## Important Concept: Coordinate System

Medical image mein **voxel index** (e.g. (10, 5, 3)) aur **physical world coordinate** (mm) alag hain. Ye project ek `CoordinateSystem` banata hai jo:
- voxel → world (mm)
- world → voxel

convert karta hai. Iska istemal measurements (mm mein distance) aur MPR crosshair sync mein hota hai.

**Code:** `coordinate_service.py`.

---

## MPR (Multiplanar Reconstruction) Kya Hai?

Ek 3D volume se 3 alag 2D views:

| Plane | Kaise |
|-------|-------|
| **Axial** | upar se neeche (z slice) |
| **Coronal** | aage se peeche (y slice) |
| **Sagittal** | side se (x slice) |

Ye 3 views ek saath dikhte hain, aur crosshair (cross lines) sync hoti hain.

**Code:** `mpr_service.py` (backend) + `MPRWorkspace.tsx` + `PlaneViewer.tsx` (frontend).

---

## AI Segmentation (Phase 3) — Samjho Kya Hai

AI ka kaam: automatically bone (ya koi tissue) detect karna, **bina manual threshold** ke.

**Architecture:**
1. **Preprocessing** — HU clip kar ke normalize (-1 to 1)
2. **Model** — 3D U-Net (MONAI), input volume, output probability map
3. **Inference** — model se prediction
4. **Postprocessing** — probability thresh karke mask, chota components hatana
5. **Metrics** — Dice coefficient, IoU (evaluation ke liye)

**Code:** `ai/segmentation/*` (preprocessing, model, inference, postprocessing, registry, service, metrics).

> ⚠️ **Lekin working nahi** kyunki trained model (weights/checkpoint) nahi hai. Bina weights ke model random output dega. Is liye ye "architecture ready, inference pending" hai.

---

## Data Kaise Store Hota Hai?

Do jagah:

1. **Metadata** (study name, date, status, model stats) → Database (SQLite/Postgres)
2. **Binary files** (DICOM originals, volume .npz, mesh .npz) → Storage (local disk ya S3)

**Code:** `models/study.py` (DB tables) + `storage/storage_service.py` (files).

---

## Frontend Ka Framebox (Architecture)

```
App (Next.js)
├── Dashboard (home)
├── Upload page
├── Study viewer
│   ├── MPRWorkspace (4 panel: axial, coronal, sagittal, 3D)
│   │   ├── PlaneViewer (2D canvas)
│   │   └── ThreeDViewer (3D R3F)
│   └── Control panel (window/level, reconstruction, AI, measure, export)
```

**State management:** Zustand (`viewer-store.ts`) — view state (slices, window/level, opacity) ek jagah.

**Data fetching:** TanStack Query (`hooks/`) — API calls uthata hai, cache karta hai, polling karta hai.

---

## Architecture Ke Design Principles (Kya Acha Hai)

1. **Medical logic alag** — services mein sirf pure Python, HTTP se alag. Testable.
2. **3D rendering decoupled** — GLB binary transport se, DICOM processing se alag.
3. **Spatial correctness** — spacing/origin/direction hamesha preserve.
4. **Lazy AI imports** — app bina torch/monai ke chalti hai.
5. **No fabrication** — checkpoint nahi to "required" bolta hai, fake result nahi deta.

---

## Common Sawaal (FAQ)

**Q: Marching Cubes kya karta hai?**
A: Binary mask (0/1 voxels) se ek smooth surface banata hai. Simplest tareeqa: triangles nikalna jo surface define karein. Iska output ek mesh (vertices + faces) hai.

**Q: GLB vs STL vs OBJ?**
A: Teeno mesh formats. GLB = binary, web ke liye best (3D viewer use karta hai). STL = 3D printing. OBJ = text, general purpose.

**Q: Threshold 300 HU kyun?**
A: Bone 300+ HU pe hota hai. User slider se change kar sakta hai (e.g. dense bone ke liye 500).

**Q: Measurement mm mein kaise aati hai?**
A: Voxel index ko physical spacing (mm/voxel) se multiply karke. Is liye real anatomy ka size sahi aata hai.

**Q: AI bina checkpoint ke kyun nahi chalta?**
A: Neural network sirf weights (trained values) ke saath meaningful output deta hai. Weights training se aate hain (data + compute + time). Ye project mein abhi weights provide nahi hue.

---

## Seekhnay Ke Liye File Reading Order (Recommended)

1. `backend/app/services/dicom_service.py` — DICOM parsing ke liye
2. `backend/app/services/volume_service.py` — 2D → 3D
3. `backend/app/services/reconstruction_service.py` — threshold + Marching Cubes
4. `backend/app/services/mpr_service.py` — MPR planes
5. `backend/app/services/coordinate_service.py` — voxel ↔ world
6. `backend/ai/segmentation/service.py` — AI pipeline flow
7. `frontend/src/components/medical/mpr/MPRWorkspace.tsx` — viewer layout
8. `frontend/src/components/medical/ThreeDViewer.tsx` — 3D rendering

---

## Summary (Yaad Rakhne Wali Baatein)

1. CT DICOM → validate → order slices → 3D volume (HU) → threshold → Marching Cubes → mesh → 3D viewer
2. Medical correctness: spatial ordering, spacing, coordinate system — ye core hai
3. AI: architecture ready, working nahi (no checkpoint)
4. Backend (FastAPI) + Frontend (Next.js/Three.js) = full stack
5. 56 backend + 19 frontend tests pass hote hain
