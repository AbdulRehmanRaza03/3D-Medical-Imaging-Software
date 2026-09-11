"""Mesh serialization and export (STL / OBJ / GLB) via trimesh.

All exports contain the *actual* reconstructed mesh — no fake downloads.
"""
from __future__ import annotations

import io

import numpy as np
import trimesh

from app.core.exceptions import ProcessingError
from app.services.reconstruction_service import MeshData


def _to_trimesh(mesh: MeshData) -> trimesh.Trimesh:
    return trimesh.Trimesh(
        vertices=mesh.vertices.astype(np.float64),
        faces=mesh.faces,
        process=False,
    )


def export_stl(mesh: MeshData) -> bytes:
    tm = _to_trimesh(mesh)
    out = io.BytesIO()
    tm.export(out, file_type="stl")
    return out.getvalue()


def export_obj(mesh: MeshData) -> bytes:
    tm = _to_trimesh(mesh)
    out = io.BytesIO()
    tm.export(out, file_type="obj")
    return out.getvalue()


def export_glb(mesh: MeshData) -> bytes:
    tm = _to_trimesh(mesh)
    out = io.BytesIO()
    # GLB requires a scene; wrap the single mesh.
    scene = trimesh.Scene(tm)
    scene.export(out, file_type="glb")
    return out.getvalue()


EXPORTERS = {
    "stl": export_stl,
    "obj": export_obj,
    "glb": export_glb,
}


def export_mesh(mesh: MeshData, fmt: str) -> bytes:
    if fmt not in EXPORTERS:
        raise ProcessingError(f"Unsupported export format: {fmt}", code="bad_format")
    return EXPORTERS[fmt](mesh)
