from __future__ import annotations

import base64
import time

from fastapi.testclient import TestClient

from codetrap_agent.storage import load_state
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


def test_model_profiles_can_be_saved_activated_and_deleted(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    first = client.post(
        "/settings",
        data={
            "profile_name": "OpenAI",
            "base_url": "https://api.openai.com",
            "api_key": "sk-openai",
            "models": "gpt-4.1",
        },
        follow_redirects=False,
    )
    assert first.status_code == 303

    second = client.post(
        "/settings",
        data={
            "profile_name": "DeepSeek",
            "base_url": "https://api.deepseek.com",
            "api_key": "sk-deepseek",
            "models": "deepseek-v4-flash",
            "save_as_new": "on",
        },
        follow_redirects=False,
    )
    assert second.status_code == 303
    state = load_state(tmp_path)
    profiles = state["settings"]["profiles"]
    assert [profile["name"] for profile in profiles] == ["DeepSeek", "OpenAI"]
    openai = next(profile for profile in profiles if profile["name"] == "OpenAI")

    activated = client.post(f"/profiles/{openai['profile_id']}/activate", follow_redirects=False)
    assert activated.status_code == 303
    state = load_state(tmp_path)
    assert state["settings"]["active_profile_id"] == openai["profile_id"]
    assert state["settings"]["models"] == ["gpt-4.1"]

    deleted = client.post(f"/profiles/{openai['profile_id']}/delete", follow_redirects=False)
    assert deleted.status_code == 303
    state = load_state(tmp_path)
    assert len(state["settings"]["profiles"]) == 1
    assert state["settings"]["profiles"][0]["name"] == "DeepSeek"
