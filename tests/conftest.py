from __future__ import annotations

import asyncio
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient

from laya_serve.core.config import Settings
from laya_serve.main import create_app


class FakeEngine:
    ready: ClassVar[bool] = True
    loaded_models: ClassVar[list[str]] = ["english"]

    def predict(self, state, questions, **kwargs):
        return {
            "model": "laya-rl-agent",
            "answers": {"department": {"type": "choice", "choice": "billing"}},
            "usage": {"input_tokens": 4, "output_tokens": 0},
            "routing": {"model": kwargs.get("model", "english")},
        }

    def predict_batch(self, states, questions, **kwargs):
        return [self.predict(state, questions, **kwargs) for state in states]


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    app.state.settings = Settings(preload=False, max_concurrent=2)
    app.state.engine = FakeEngine()
    app.state.inference_semaphore = asyncio.Semaphore(2)
    return TestClient(app)
