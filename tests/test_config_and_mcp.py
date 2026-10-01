from __future__ import annotations

from fastapi import HTTPException

from laya_serve.core.config import Settings
from laya_serve.modules.mcp.server import predict_decision


def test_laya_environment_prefix_and_csv_settings():
    settings = Settings(_env_file=None, models="english,multilingual", cors_origins="https://a,https://b")
    assert settings.models == ("english", "multilingual")
    assert settings.cors_origins == ("https://a", "https://b")


def test_csv_environment_values_do_not_require_json(monkeypatch):
    monkeypatch.setenv("LAYA_MODELS", "english,multilingual")
    monkeypatch.setenv("LAYA_CORS_ORIGINS", "https://studio.example,https://api.example")
    settings = Settings(_env_file=None)
    assert settings.models == ("english", "multilingual")
    assert settings.cors_origins == ("https://studio.example", "https://api.example")


def test_mcp_prediction_reuses_validation_before_engine_load(monkeypatch):
    from laya_serve.modules.mcp import server

    monkeypatch.setattr(server, "get_settings", lambda: Settings(max_state_chars=3))
    try:
        predict_decision("too long", {})
    except HTTPException as exc:
        assert exc.status_code == 413
    else:
        raise AssertionError("oversized MCP input must be rejected before loading an engine")
