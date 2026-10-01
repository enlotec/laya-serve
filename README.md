# Laya Serve

Production-ready REST and MCP wrapper for [Laya](https://github.com/NandhaKishorM/laya), Convai Innovations' Apache-2.0, open-source System One decision model. It exposes Laya's typed-decision protocol with explicit readiness, bounded concurrency, typed configuration, and reproducible CPU/GPU containers.

## Run locally

Python 3.14 is required.

```powershell
uv venv --python 3.14
uv pip install -e ".[dev]"
enlotec-laya-serve
```

The first run downloads configured Hugging Face checkpoints. The service binds to `http://localhost:8089`; `/ready` returns success only after loading is complete.

```powershell
docker compose up --build
docker compose -f docker-compose.yaml -f docker-compose.gpu.yaml up --build
```

## HTTP API

`POST /v1/systemone` accepts Laya's typed-decision request and response shape:

```json
{
  "state": {"body": "We were billed twice. Please refund us."},
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which team should handle this?",
      "criteria": {"billing": "refunds and payments", "technical": "bugs and outages"}
    },
    "urgency": {
      "type": "score",
      "instructions": "How urgent is this?",
      "criteria": ["low", "normal", "critical"]
    },
    "churn_risk": {
      "type": "noul",
      "instructions": "Does the customer threaten to cancel?"
    }
  }
}
```

`POST /v1/systemone/batch` accepts the same `questions` with `states`. `GET /health`, `GET /ready`, and `GET /v1/models` are available for operations.

Use `LAYA_API_KEY` to require `Authorization: Bearer <key>`. Settings are documented in [`.env.example`](.env.example).
Set `LAYA_REVISION` to a reviewed Hugging Face commit or tag in a production deployment; the
selected revision is included in `GET /v1/models`.

## MCP

Run the stdio MCP server with:

```powershell
enlotec-laya-serve-mcp
```

It provides `laya_predict` and `laya_status`, sharing the same Laya configuration and validation as REST.
The HTTP SSE transport is mounted at `http://localhost:8089/mcp/sse` (messages:
`/mcp/messages/`). When `LAYA_API_KEY` is configured, both REST and MCP HTTP requests require
the bearer token.

## Development

```powershell
uv run pytest
uv run ruff check .
```

This package intentionally fails startup if real Laya checkpoints cannot load; it never synthesizes model responses.
