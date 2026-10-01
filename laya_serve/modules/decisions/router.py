"""HTTP decision endpoints."""

from __future__ import annotations

import asyncio
import hmac
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from laya_serve.modules.decisions.schemas import BatchDecisionRequest, DecisionRequest
from laya_serve.modules.decisions.service import predict, predict_batch

router = APIRouter(tags=["System One"])


def _authenticate(authorization: str | None, request: Request) -> None:
    api_key = request.app.state.settings.api_key
    if api_key is None:
        return
    expected = f"Bearer {api_key.get_secret_value()}"
    if not hmac.compare_digest(authorization or "", expected):
        raise HTTPException(401, "invalid or missing bearer token")


async def _run(request: Request, func: Any, payload: Any) -> Any:
    semaphore: asyncio.Semaphore = request.app.state.inference_semaphore
    if semaphore.locked():
        raise HTTPException(503, "server busy, try again later", headers={"Retry-After": "1"})
    async with semaphore:
        try:
            return await asyncio.to_thread(func, request.app.state.engine, payload, request.app.state.settings)
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except Exception as exc:
            raise HTTPException(500, "inference failed") from exc


@router.post("/v1/systemone")
async def systemone(payload: DecisionRequest, request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _authenticate(authorization, request)
    return await _run(request, predict, payload)


@router.post("/v1/systemone/batch")
async def systemone_batch(payload: BatchDecisionRequest, request: Request, authorization: str | None = Header(default=None)) -> list[dict[str, Any]]:
    _authenticate(authorization, request)
    return await _run(request, predict_batch, payload)
