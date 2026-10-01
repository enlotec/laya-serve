"""Thin, testable adapter around Laya's public Router SDK."""

from __future__ import annotations

import os
from typing import Any

import structlog

from laya_serve.core.config import Settings

logger = structlog.get_logger(__name__)


class LayaEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.router: Any | None = None
        self.ready = False

    def load(self) -> None:
        """Create and preload exactly the configured upstream checkpoints."""
        if self.settings.threads:
            import torch

            torch.set_num_threads(self.settings.threads)
        os.environ.setdefault("USE_TF", "0")
        from laya import Router

        self.router = Router(
            device=None if self.settings.device == "auto" else self.settings.device,
            max_loaded=max(self.settings.max_loaded, len(self.settings.models)),
            auto_task_detection=self.settings.auto_task_detection,
            revision=self.settings.revision,
        )
        if self.settings.preload:
            self.router.preload(list(self.settings.models))
        self.ready = True
        logger.info("laya_engine_ready", loaded=getattr(self.router, "loaded", []))

    def predict(self, state: Any, questions: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        if not self.ready or self.router is None:
            raise RuntimeError("Laya engine is not ready")
        return self.router.predict(state, questions, **kwargs)

    def predict_batch(self, states: list[Any], questions: dict[str, Any], **kwargs: Any) -> list[dict[str, Any]]:
        if not self.ready or self.router is None:
            raise RuntimeError("Laya engine is not ready")
        return self.router.predict_batch(states, questions, **kwargs)

    @property
    def loaded_models(self) -> list[str]:
        return list(getattr(self.router, "loaded", []) or [])
