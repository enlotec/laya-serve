"""Pydantic wire contracts for typed-decision endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Any
    questions: dict[str, dict[str, Any]]
    model: str | None = None
    task: str | None = None
    lang: str | None = None
    lang_guess: str | None = None
    min_confidence: float | None = Field(default=None, ge=0, le=1)
    max_len: int | None = Field(default=None, ge=1)
    head_max_len: int | None = Field(default=None, ge=1)


class BatchDecisionRequest(DecisionRequest):
    state: Any = None
    states: list[Any] = Field(min_length=1)
    batch_size: int | None = Field(default=None, ge=1)
    sort_by_length: bool = False
