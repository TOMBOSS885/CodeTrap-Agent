"""Prompt construction for adversarial problem generation."""

from __future__ import annotations

from .constants import TRAP_DIMENSIONS


PROMPT_LIBRARY = {
    "role": (
        "你是一个专门为代码生成 AI 设计对抗性编程题的出题专家。"
        "你的目标不是出偏题，而是出规则清楚、答案唯一、测试强、容易让模型误判细节的题。"
    ),
    "quality_bar": (
        "题目必须自洽、可执行、可自动判题。不要依赖随机、网络、文件系统、时间、浮点误差或人类主观解释。"
        "如果用户提示词太宽泛，你要自行收束成一个具体函数题。"
    ),
    "trap_strategy": (
        "优先制造这些失败模式：边界条件被忽略、样例误导、重复元素处理错误、稳定顺序被破坏、"
        "空输入/单元素错误、贪心看似成立但实际不成立、复杂度在隐藏用例爆炸、状态被错误复用。"
    ),
    "answer_contract": (
        "reference_solution 必须是完整 Python 代码，只定义题目函数和必要 helper；"
        "tests 中的 kwargs 必须能直接传给 signature 中的函数；expected 必须是 JSON 可表达的确定值。"
    ),
}


def build_generation_prompt(topic: str, count: int, language: str, difficulty: str) -> str:
    dimensions = "\n".join(f"- {name}" for name in TRAP_DIMENSIONS)
    return f"""
{PROMPT_LIBRARY["role"]}

用户原始出题提示词：
{topic}

生成数量：{count}
目标语言：{language}
难度：{difficulty}

提示词库规则：
1. {PROMPT_LIBRARY["quality_bar"]}
2. {PROMPT_LIBRARY["trap_strategy"]}
3. {PROMPT_LIBRARY["answer_contract"]}
4. 题面必须明确函数签名、参数含义、返回值、所有边界行为和约束。
5. 每道题至少 8 个测试，其中 public 至少 3 个，hidden 至少 5 个。
6. public tests 是给用户看的样例；hidden tests 是专门卡 AI 常见错误的测试。
7. 每道题至少 5 个 pitfalls，每个坑点必须写清：
   - 错误诱因
   - 常见错误解法
   - 会被哪些测试抓住
8. adversarial_notes 必须说明这道题如何补足普通题库不足，以及它主要针对哪些 AI 失败模式。
9. 尽量覆盖下面陷阱维度，不能只写普通边界条件：
{dimensions}

只输出 JSON，不要 Markdown，不要解释文字。格式必须严格如下：
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
