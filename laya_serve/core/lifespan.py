"""Application lifecycle management."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from laya_serve.core.config import get_settings
from laya_serve.core.engine import LayaEngine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = LayaEngine(settings)
    engine.load()
    app.state.settings = settings
    app.state.engine = engine
    yield
    engine.ready = False
