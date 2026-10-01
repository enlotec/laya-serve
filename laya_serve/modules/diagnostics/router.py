"""Liveness, readiness, and model inventory endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from laya_serve import __version__

router = APIRouter(tags=["Diagnostics"])


@router.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "version": __version__}


@router.get("/ready")
async def ready(request: Request) -> dict[str, object]:
    engine = getattr(request.app.state, "engine", None)
    return {"status": "ready" if engine and engine.ready else "starting", "loaded": engine.loaded_models if engine else []}


@router.get("/v1/models")
async def models(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    engine = request.app.state.engine
    return {
        "configured": list(settings.models),
        "loaded": engine.loaded_models,
        "device": settings.device,
        "revision": settings.revision,
    }
