from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass

from codetrap.core.problem import ProblemVariant
from codetrap.llm.prompt import build_problem_prompt


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "none"
    api_key: str = ""
    model: str = ""
    api_base: str = ""


class LLMProblemGenerator:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def enabled(self) -> bool:
        return self.config.provider not in {"", "none"} and bool(self.config.api_key)

    def generate_variant(self, family, sources) -> tuple[ProblemVariant | None, str]:
        if not self.enabled():
            return None, "llm_disabled"
        prompt = build_problem_prompt(
            family.title,
            family.input_format,
            family.output_format,
            family.trap_notes(),
            [source.model_dump() for source in sources],
        )
        try:
            text = self._complete(prompt)
            data = _extract_json(text)
            return ProblemVariant(
                id="llm-generated",
                title=str(data["title"])[:120],
                statement=str(data["statement"]),
                tags=[str(x) for x in data.get("tags", [])][:8],
            ), "llm_ok"
        except Exception as exc:
            return None, f"llm_failed:{type(exc).__name__}"

    def _complete(self, prompt: str) -> str:
        provider = self.config.provider
        if provider in {"openai", "openai_compatible", "deepseek", "qwen", "moonshot", "zhipu"}:
            return self._openai_compatible(prompt)
        if provider == "anthropic":
            return self._anthropic(prompt)
        if provider == "gemini":
            return self._gemini(prompt)
        raise ValueError(f"unsupported provider: {provider}")

    def _openai_compatible(self, prompt: str) -> str:
        base = self.config.api_base or _default_openai_base(self.config.provider)
        model = self.config.model or _default_model(self.config.provider)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你只输出严格 JSON。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }
        data = _post_json(f"{base.rstrip('/')}/chat/completions", payload, {"Authorization": f"Bearer {self.config.api_key}"})
        return data["choices"][0]["message"]["content"]

    def _anthropic(self, prompt: str) -> str:
        base = self.config.api_base or "https://api.anthropic.com/v1"
        model = self.config.model or "claude-3-5-sonnet-latest"
        payload = {
            "model": model,
            "max_tokens": 1200,
            "temperature": 0.7,
            "messages": [{"role": "user", "content": prompt}],
        }
        data = _post_json(
            f"{base.rstrip('/')}/messages",
            payload,
            {"x-api-key": self.config.api_key, "anthropic-version": "2023-06-01"},
        )
        return "".join(part.get("text", "") for part in data.get("content", []))

    def _gemini(self, prompt: str) -> str:
        base = self.config.api_base or "https://generativelanguage.googleapis.com/v1beta"
        model = self.config.model or "gemini-1.5-pro"
        url = f"{base.rstrip('/')}/models/{model}:generateContent?key={self.config.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7}}
        data = _post_json(url, payload, {})
        return data["candidates"][0]["content"]["parts"][0]["text"]


def _post_json(url: str, payload: dict, headers: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end >= start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _default_openai_base(provider: str) -> str:
    defaults = {
        "openai": "https://api.openai.com/v1",
        "openai_compatible": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "moonshot": "https://api.moonshot.cn/v1",
        "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    }
    return defaults.get(provider, "https://api.openai.com/v1")


def _default_model(provider: str) -> str:
    defaults = {
        "openai": "gpt-4o-mini",
        "openai_compatible": "gpt-4o-mini",
        "deepseek": "deepseek-chat",
        "qwen": "qwen-plus",
        "moonshot": "moonshot-v1-8k",
        "zhipu": "glm-4-flash",
    }
    return defaults.get(provider, "gpt-4o-mini")

