# Phase 1 Scope & Status

Phase 1 delivers the **Medical 3D Imaging Core** — a real DICOM-to-3D pipeline
and interactive viewer.

## Completed

| Area | Status |
| ---- | ------ |
| DICOM upload & validation | ✅ |
| CT series detection | ✅ |
| Spatial slice ordering | ✅ |
| Metadata extraction | ✅ |
| 3D volume construction (HU, spacing/origin/direction) | ✅ |
| 2D axial slice viewer | ✅ |
| Window/level (presets + custom) | ✅ |
| Bone surface reconstruction | ✅ |
| Marching Cubes (spacing-aware) | ✅ |
| Mesh cleanup | ✅ |
| Interactive 3D viewer | ✅ |
| Distance & angle measurements | ✅ |
| STL / OBJ / GLB export | ✅ |
| Study management + processing jobs | ✅ |
| Automated tests (backend + frontend) | ✅ |
| Documentation | ✅ |

## Explicitly out of scope (not mocked)

- MPR (sagittal/coronal) reconstruction — Phase 2
- AI segmentation (MONAI / 3D U-Net) — Phase 3
- Advanced analysis (ICP, deviation maps, symmetry) — Phase 4
- Orthopaedic implant/surgical planning — Phase 5
- Research platform (projects, annotations, collaboration) — Phase 6
- AI assistant (natural-language query) — Phase 7

## Definition of Done

Phase 1 is complete when a user can take a real de-identified CT DICOM dataset
and: upload it → detect the CT series → order slices → extract metadata →
build a volume → browse axial slices → reconstruct a bone surface → view the
mesh in 3D → measure distance/angle → export the real mesh — with errors and
progress handled throughout and automated tests passing.
