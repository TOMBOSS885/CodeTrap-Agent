from __future__ import annotations

import base64
import time

from fastapi.testclient import TestClient

from codetrap_agent.web_app import create_app


def test_optional_basic_auth(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CODETRAP_PASSWORD", "secret")
    client = TestClient(create_app(tmp_path))

    assert client.get("/").status_code == 401

    token = base64.b64encode(b"admin:secret").decode("ascii")
    response = client.get("/", headers={"Authorization": f"Basic {token}"})
    assert response.status_code == 200


def test_saved_api_key_can_be_left_blank(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    first = client.post(
        "/settings",
        data={
            "base_url": "https://api.example.com",
            "api_key": "sk-test",
            "models": "model-a",
        },
        follow_redirects=False,
    )
    assert first.status_code == 303

    second = client.post(
        "/settings",
        data={
            "base_url": "https://api.example.com",
            "api_key": "",
            "models": "model-b",
        },
        follow_redirects=False,
    )
    assert second.status_code == 303


def test_generation_job_reports_missing_model_settings(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    response = client.post(
        "/generate",
        data={"topic": "字符串解析", "count": "1", "difficulty": "hard"},
        headers={"Accept": "application/json", "X-Requested-With": "fetch"},
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    for _ in range(20):
        status = client.get(f"/jobs/{job_id}").json()
        if status["status"] == "failed":
            break
        time.sleep(0.05)

    assert status["status"] == "failed"
    assert status["error"]
