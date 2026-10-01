"""Shared validation and synchronous inference boundary."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from laya_serve.core.config import Settings
from laya_serve.core.engine import LayaEngine


def validate_request(state: Any, questions: dict[str, Any], settings: Settings) -> None:
    if len(questions) > settings.max_questions:
        raise HTTPException(413, f"too many questions ({len(questions)} > {settings.max_questions})")
    try:
        state_size = len(state) if isinstance(state, str) else len(json.dumps(state, ensure_ascii=False))
    except (TypeError, ValueError, RecursionError) as exc:
        raise HTTPException(400, "state must be JSON-serializable") from exc
    if state_size > settings.max_state_chars:
        raise HTTPException(413, f"state too large ({state_size} > {settings.max_state_chars} chars)")


def prediction_kwargs(payload: Any, settings: Settings) -> dict[str, Any]:
    values = {
        key: getattr(payload, key)
        for key in ("model", "task", "lang", "lang_guess", "min_confidence", "max_len", "head_max_len")
        if getattr(payload, key, None) is not None
    }
    for key in ("max_len", "head_max_len"):
        if values.get(key, 0) > settings.max_token_budget:
            raise HTTPException(422, f"{key} exceeds configured maximum token budget")
    return values


def predict(engine: LayaEngine, payload: Any, settings: Settings) -> dict[str, Any]:
    validate_request(payload.state, payload.questions, settings)
    return engine.predict(payload.state, payload.questions, **prediction_kwargs(payload, settings))


def predict_batch(engine: LayaEngine, payload: Any, settings: Settings) -> list[dict[str, Any]]:
    if len(payload.states) > settings.max_batch_states:
        raise HTTPException(413, f"too many batch states ({len(payload.states)} > {settings.max_batch_states})")
    for state in payload.states:
        validate_request(state, payload.questions, settings)
    kwargs = prediction_kwargs(payload, settings)
    if payload.batch_size is not None:
        kwargs["batch_size"] = payload.batch_size
    if payload.sort_by_length:
        kwargs["sort_by_length"] = True
    return engine.predict_batch(payload.states, payload.questions, **kwargs)
