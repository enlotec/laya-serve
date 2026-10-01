"""MCP stdio server backed by the same Laya engine abstraction."""

from __future__ import annotations

from typing import Any

from laya_serve.core.config import get_settings
from laya_serve.core.engine import LayaEngine
from laya_serve.modules.decisions.service import validate_request

_engine: LayaEngine | None = None


def get_engine() -> LayaEngine:
    global _engine
    if _engine is None:
        _engine = LayaEngine(get_settings())
        _engine.load()
    return _engine


def predict_decision(state: Any, questions: dict[str, dict[str, Any]], model: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    validate_request(state, questions, settings)
    kwargs = {"model": model} if model else {}
    return get_engine().predict(state, questions, **kwargs)


from mcp.server import MCPServer

mcp = MCPServer("Laya Serve")


@mcp.tool()
def laya_predict(
    state: Any, questions: dict[str, dict[str, Any]], model: str | None = None
) -> dict[str, Any]:
    """Answer typed choice, score, and yes/no questions using Laya."""
    return predict_decision(state, questions, model)


@mcp.tool()
def laya_status() -> dict[str, Any]:
    """Report the checkpoints currently loaded by the Laya service."""
    engine = get_engine()
    return {"status": "ready", "loaded": engine.loaded_models}


def run_stdio() -> None:
    mcp.run(transport="stdio")
