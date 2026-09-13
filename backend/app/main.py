"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import jobs, models, mpr, segmentation, slices, studies
from app.core.config import settings
from app.core.exceptions import OrthoVisionError
from app.core.logging import configure_logging
from app.db.session import init_db

logger = logging.getLogger(__name__)

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("OrthoVision AI backend started.")
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "OrthoVision AI — medical imaging research and visualization platform. "
        "Not a diagnostic device."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(OrthoVisionError)
async def orthovision_error_handler(request: Request, exc: OrthoVisionError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log the full error server-side; never leak stack traces to the client.
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",
            "code": "internal_error",
        },
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


app.include_router(studies.router, prefix=settings.api_prefix)
app.include_router(slices.router, prefix=settings.api_prefix)
app.include_router(mpr.router, prefix=settings.api_prefix)
app.include_router(models.router, prefix=settings.api_prefix)
app.include_router(jobs.router, prefix=settings.api_prefix)
app.include_router(segmentation.router, prefix=settings.api_prefix)
