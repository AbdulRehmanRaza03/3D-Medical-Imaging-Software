# AI Segmentation — Inference Architecture

OrthoVision AI uses a clean, pluggable AI segmentation architecture separated
from the web/HTTP and DICOM pipelines.

## Package layout

```
backend/ai/segmentation/
  __init__.py
  config.py          # PreprocessingConfig, InferenceConfig, PostProcessingConfig, labels
  schemas.py         # Pydantic API contracts
  exceptions.py      # SegRuntimeUnavailableError, ModelCheckpointMissingError, ...
  registry.py        # model registry (bone_1, future femur/pelvis/hip)
  model.py           # 3D U-Net (MONAI) + build_model_for
  preprocessing.py   # HU clip, normalize, padding, tensor conversion
  inference.py       # device resolution, checkpoint load, sliding-window
  postprocessing.py  # argmax, threshold, component filtering, hole fill
  metrics.py         # Dice, IoU, precision, recall
  service.py         # end-to-end orchestration + label stats
```

## Model abstraction

Every model is described by a `RegisteredModel` with:

- `id`, `name`, `version`, `task`
- `labels` (e.g. `background` + `bone`)
- `framework`, `architecture` (`unet3d`, …)
- `target_spacing`, `checkpoint_filename`

New models are added to `registry.REGISTERED_MODELS` without touching the
inference pipeline. A model is only "available" when its checkpoint file
actually exists on disk.

## Lazy imports

All `torch`/`monai` imports happen inside functions (not at module import time),
so the application boots and serves Phases 1–2 even when the ML runtime is
missing. Segmentation then returns a clear, actionable error instead of
crashing the app.

## Device handling

`resolve_device("auto")` picks CUDA when available, else CPU. Never mandatory.

## Sliding-window inference

For volumes too large for memory, `run_sliding_window` uses MONAI's
`sliding_window_inference` with a configurable `roi_size`, `overlap`, and
`sw_batch_size`.

## Coordinate integrity

Preprocessing may pad the volume to a divisible size; the padding is stripped
after inference so the output mask shape exactly matches the source volume, and
the segmentation remains aligned with the canonical CT coordinate system.

## Where a checkpoint is supplied

Place the trained weights at `backend/ai/segmentation/models/bone_1.pt` (or set
`OV_MODELS_DIR` to a custom models directory). The checkpoint can be either a
raw state dict or a dict with a `model_state_dict` / `state_dict` key.
