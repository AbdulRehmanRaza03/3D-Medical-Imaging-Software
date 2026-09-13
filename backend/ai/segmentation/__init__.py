"""AI segmentation package.

This package implements the AI-powered anatomical segmentation pipeline for
OrthoVision AI Phase 3. It is designed so the heavy dependencies (PyTorch +
MONAI) are imported lazily — the application boots and serves all Phase 1/2
functionality even when the ML runtime is unavailable, and only falls back to a
clear, actionable error when segmentation is requested.
"""
