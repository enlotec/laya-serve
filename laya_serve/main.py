"""ASGI entrypoint."""

from __future__ import annotations

import asyncio
import hmac

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from laya_serve import __version__
from laya_serve.core.config import get_settings
from laya_serve.core.lifespan import lifespan
from laya_serve.modules.decisions.router import router as decisions_router
from laya_serve.modules.diagnostics.router import router as diagnostics_router
from laya_serve.modules.mcp.server import mcp


def create_app() -> FastAPI:
    app = FastAPI(title="Laya Serve", version=__version__, lifespan=lifespan)
    settings = get_settings()
    app.state.inference_semaphore = asyncio.Semaphore(settings.max_concurrent)
    if settings.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["*"], allow_headers=["*"])
    app.include_router(diagnostics_router)
    app.include_router(decisions_router)

    @app.middleware("http")
    async def protect_mcp(request, call_next):
        current_settings = getattr(request.app.state, "settings", settings)
        if request.url.path.startswith("/mcp") and current_settings.api_key is not None:
            expected = f"Bearer {current_settings.api_key.get_secret_value()}"
            if not hmac.compare_digest(request.headers.get("authorization", ""), expected):
                from fastapi.responses import JSONResponse

                return JSONResponse({"detail": "invalid or missing bearer token"}, status_code=401)
        return await call_next(request)

    app.mount("/mcp", mcp.sse_app(host=settings.host, max_request_body_size=settings.max_body_bytes))
    return app


app = create_app()


def cli() -> None:
    settings = get_settings()
    uvicorn.run("laya_serve.main:app", host=settings.host, port=settings.port, log_level=settings.log_level)
