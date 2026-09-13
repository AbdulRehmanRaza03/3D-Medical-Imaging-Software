# Phase 3 — AI-Powered 3D Medical Image Segmentation

Phase 3 adds AI-powered anatomical segmentation to OrthoVision AI using
PyTorch + MONAI.

## What was added

| Area | Feature |
| ---- | ------- |
| **AI pipeline** | Preprocessing → inference → post-processing → mask → metrics |
| **Model registry** | Pluggable model registry (`bone_1`, future femur/pelvis/hip) |
| **3D U-Net** | MONAI UNet architecture, swappable (UNETR/SegResNet/Swin) |
| **Inference** | CPU/GPU auto-detection, sliding-window support |
| **Storage** | Segmentation mask persistence + per-label physical volume/bbox/centroid |
| **Jobs** | Segmentation jobs integrated into the existing job system |
| **API** | Model list, job create/status, result list/get/delete |
| **Frontend** | AI Segmentation panel in the workstation control sidebar |

## Model checkpoint requirement

**A pretrained model checkpoint is required for meaningful segmentation.**
The pipeline is fully implemented, but no weights are shipped. The `bone_1`
model is registered with `checkpoint_filename="bone_1.pt"`; placing a
checkpoint file at `backend/ai/segmentation/models/bone_1.pt` makes it
available for inference.

Until then, the API and UI correctly report **"Model checkpoint required"**
(they do not fabricate results).

## Runtime requirement

`torch` requires the Microsoft Visual C++ Redistributable on Windows. Without
it, `import torch` fails with a missing `msvcp140.dll` error and segmentation
returns an actionable `seg_runtime_unavailable` error.

## Inference pipeline

```
Canonical CT volume (Phase 1, (D,H,W) HU)
  → clip HU [-1024, 3071]
  → normalize min-max [-1, 1]
  → (1,1,D,H,W) tensor, pad to divisible
  → model inference (CPU/GPU)
  → softmax
  → argmax → binary mask
  → post-process (largest component, small-component removal)
  → physical volume / bbox / centroid per label
```

The original CT geometry (spacing/origin/direction) is preserved throughout so
the segmentation remains spatially aligned with the source volume.

## Known limitations

- No trained checkpoint is shipped; segmentation requires a real checkpoint.
- `torch` is not importable on this machine until the MSVC runtime is installed.
- Overlay rendering on the MPR planes is designed but not yet wired to a live
  mask (the mask is exposed via the result API + storage; the overlay hookup is
  the remaining integration step).
- Metrics (Dice/IoU) are computed only against ground truth; no accuracy is
  claimed for inference without annotations.
