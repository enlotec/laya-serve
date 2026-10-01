PAYLOAD = {
    "state": {"body": "We were charged twice"},
    "questions": {
        "department": {
            "type": "choice",
            "instructions": "Which team should handle this?",
            "criteria": {"billing": "refunds", "technical": "bugs"},
        }
    },
}


def test_health_and_ready(client):
    assert client.get("/health").json()["status"] == "ok"
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["loaded"] == ["english"]


def test_systemone_preserves_laya_shaped_response(client):
    response = client.post("/v1/systemone", json=PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["answers"]["department"]["choice"] == "billing"
    assert body["usage"]["output_tokens"] == 0


def test_batch_preserves_input_order(client):
    response = client.post(
        "/v1/systemone/batch", json={**PAYLOAD, "states": ["first", "second"]}
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_size_limit_returns_client_error(client):
    client.app.state.settings.max_state_chars = 5
    response = client.post("/v1/systemone", json=PAYLOAD)
    assert response.status_code == 413


def test_api_key_is_enforced(client):
    from pydantic import SecretStr

    client.app.state.settings.api_key = SecretStr("secret")
    assert client.post("/v1/systemone", json=PAYLOAD).status_code == 401
    authorized = client.post(
        "/v1/systemone", json=PAYLOAD, headers={"Authorization": "Bearer secret"}
    )
    assert authorized.status_code == 200
    assert client.get("/mcp/sse").status_code == 401
