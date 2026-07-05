"""Prompt construction for adversarial problem generation."""

from __future__ import annotations

from .constants import TRAP_DIMENSIONS


def build_generation_prompt(topic: str, count: int, language: str, difficulty: str) -> str:
    dimensions = "\n".join(f"- {name}" for name in TRAP_DIMENSIONS)
    return f"""
你是 CodeTrap-Agent 的出题模型。请生成 {count} 道用于难住代码生成 AI 的编程题。

主题：{topic}
目标语言：{language}
难度：{difficulty}

要求：
1. 每道题必须可用一个 Python 函数求解，函数签名写在 signature 字段。
2. reference_solution 必须给出完整 Python 代码，只允许定义题目要求的函数和必要 helper。
3. tests 至少 8 个，其中 public 至少 3 个，hidden 至少 5 个。每个测试包含 name、visibility、kwargs、expected、purpose。
4. pitfalls 至少 5 个，必须写明错误诱因、常见错误解法、对应测试名。
5. adversarial_notes 解释为什么它能补足普通题库不足，并尽可能针对 AI 常犯模式。
6. 尽量覆盖下面陷阱维度，不能只做普通边界条件：
{dimensions}

只输出 JSON，不要 Markdown。格式如下：
{{
  "problems": [
    {{
      "title": "...",
      "topic": "...",
      "difficulty": "...",
      "statement": "...",
      "signature": "def solve(...):",
      "reference_solution": "...",
      "tests": [
        {{
          "name": "...",
          "visibility": "public|hidden",
          "kwargs": {{}},
          "expected": null,
          "purpose": "..."
        }}
      ],
      "pitfalls": [
        {{
          "name": "...",
          "dimension": "off_by_one",
          "description": "...",
          "likely_wrong_solution": "...",
          "caught_by": ["..."]
        }}
      ],
      "adversarial_notes": "..."
    }}
  ]
}}
""".strip()
