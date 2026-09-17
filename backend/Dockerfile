# OrthoVision AI backend — production image.
#
# Build:  docker build -t orthovision-backend .
# Run:    docker run -p 8000:8000 --env-file .env orthovision-backend

FROM python:3.14-slim

# Non-root user for security.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STORAGE_DIR=/data/storage

WORKDIR /app

# Install system deps required by scikit-image / Pillow / trimesh.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        libglib2.0-0 \
        libgl1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies first (better layer caching).
COPY requirements.txt requirements-storage.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements-storage.txt

# Application source.
COPY app ./app
COPY ai ./ai

# AI segmentation is gated at runtime by checkpoint availability AND torch/MONAI
# presence. The ``ai`` package is copied (it is imported by the API layer), but
# the heavy runtime (torch/MONAI) is NOT installed in this image — the app
# reports "Model checkpoint required" / "runtime unavailable" gracefully.
# To actually run AI inference, build the worker image (Dockerfile.worker) with
# requirements-ai.txt installed and a checkpoint present.

# Persistable volume (bind mount in production or use S3 backend).
RUN mkdir -p /data/storage

EXPOSE 8000

# Run with Uvicorn. --host 0.0.0.0 is required inside a container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
