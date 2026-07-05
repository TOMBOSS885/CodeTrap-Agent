from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from codetrap_agent.web_app import create_app


def test_optional_basic_auth(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CODETRAP_PASSWORD", "secret")
    client = TestClient(create_app(tmp_path))

    assert client.get("/").status_code == 401

    token = base64.b64encode(b"admin:secret").decode("ascii")
    response = client.get("/", headers={"Authorization": f"Basic {token}"})
    assert response.status_code == 200
