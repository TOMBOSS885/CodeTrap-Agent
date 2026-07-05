"""OpenAI-compatible model client."""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .config import RuntimeConfig
from .constants import DEFAULT_MODEL_TEMPERATURE, DEFAULT_TOP_P


@dataclass(frozen=True)
class ModelResult:
    request_raw: dict[str, Any]
    response_raw: dict[str, Any]
    content: str


class ModelAPIError(RuntimeError):
    def __init__(self, message: str, request_raw: dict[str, Any], response_raw: dict[str, Any]) -> None:
        super().__init__(message)
        self.request_raw = request_raw
        self.response_raw = response_raw


def build_request_raw(config: RuntimeConfig, model: str, prompt: str) -> dict[str, Any]:
    return {
        "schema_version": "codetrap-agent.api_request.v1",
        "provider_api": "openai_chat_completions",
        "method": "POST",
        "url": f"{config.base_url.rstrip('/')}/chat/completions",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer [REDACTED]" if config.api_key_set else "",
        },
        "body": {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": DEFAULT_MODEL_TEMPERATURE,
            "top_p": DEFAULT_TOP_P,
            "stream": False,
        },
    }


def real_completion(config: RuntimeConfig, model: str, prompt: str, timeout: float = 90.0) -> ModelResult:
    request_raw = build_request_raw(config, model, prompt)
    if not config.base_url:
        raise ModelAPIError("base_url is not configured", request_raw, {})
    if not config.api_key:
        raise ModelAPIError("api_key is not configured", request_raw, {})
    request = urllib.request.Request(
        request_raw["url"],
        data=json.dumps(request_raw["body"], ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {config.api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, socket.timeout) as exc:
        response_raw = {"error_type": "timeout", "error": f"timeout after {timeout:g}s"}
        raise ModelAPIError("model request timed out", request_raw, response_raw) from exc
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        response_raw = {"error_type": "http_error", "status_code": exc.code, "error": detail[:1000]}
        raise ModelAPIError(f"model request failed: HTTP {exc.code}", request_raw, response_raw) from exc
    except urllib.error.URLError as exc:
        response_raw = {"error_type": "url_error", "error": str(exc.reason)}
        raise ModelAPIError("model request failed", request_raw, response_raw) from exc
    payload.setdefault("schema_version", "codetrap-agent.api_response.v1")
    payload.setdefault("created_at", int(time.time()))
    choices = payload.get("choices") or []
    content = ""
    if choices and isinstance(choices[0], dict):
        content = str((choices[0].get("message") or {}).get("content", ""))
    return ModelResult(request_raw=request_raw, response_raw=payload, content=content)
