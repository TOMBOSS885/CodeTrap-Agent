from __future__ import annotations

from codetrap.core.problem import ProblemVariant


def build_problem_prompt(
    family_title: str,
    input_format: str,
    output_format: str,
    traps: list[str],
    sources: list[dict],
) -> str:
    source_text = "\n".join(
        f"- 标题：{item.get('title', '')}\n  摘要：{item.get('snippet', '')}\n  链接：{item.get('url', '')}"
        for item in sources[:6]
    ) or "- 没有可用在线来源，请基于题型和陷阱要求原创生成。"
    trap_text = "\n".join(f"- {item}" for item in traps)
    return f"""你是资深算法竞赛出题人，尤其擅长设计让编程大模型出错的“坑题”。

你的任务：为给定题型生成一道原创中文编程题题面。题目要更像真实在线评测题，而不是模板改写。

固定题型：{family_title}
固定输入 JSON schema：{input_format}
固定输出 JSON schema：{output_format}

硬性约束：
1. 只生成题面元信息，不生成测试用例，不生成参考答案代码。
2. 不能改变输入 JSON schema 和输出 JSON schema，否则系统无法自动评测。
3. 题面必须原创，不得复制搜索结果原文。
4. 题面必须包含清晰的非法输入处理规则、边界条件和判定细节。
5. 至少设计 8 个容易让 AI 写错的坑点，并自然融入题面规则。
6. 题目不能含糊，必须让一个普通程序员能按题面独立实现。
7. 返回严格 JSON，不要 Markdown，不要解释文字，不要代码块。

本题型已有核心坑点：
{trap_text}

联网搜索到的相关素材，仅用于启发，不可照抄：
{source_text}

请返回如下 JSON：
{{
  "title": "中文题目标题，具体、有场景感",
  "statement": "完整中文题面。必须包含：背景、任务、输入对象说明、输出规则、非法输入处理、至少 8 个边界/坑点说明。",
  "tags": ["中文标签1", "中文标签2", "adversarial"]
}}
"""


def fallback_variant(title: str, statement: str, tags: list[str]) -> ProblemVariant:
    return ProblemVariant(id="ai-fallback", title=title, statement=statement, tags=tags)
