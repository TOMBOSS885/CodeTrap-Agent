from __future__ import annotations

from codetrap.core.problem import ProblemVariant


def build_problem_prompt(family_title: str, input_format: str, output_format: str, traps: list[str], sources: list[dict]) -> str:
    source_text = "\n".join(
        f"- {item.get('title', '')}: {item.get('snippet', '')} ({item.get('url', '')})"
        for item in sources[:5]
    ) or "- 无在线来源，请基于题型本身生成。"
    trap_text = "\n".join(f"- {item}" for item in traps)
    return f"""你是算法题出题专家，目标是生成一道容易让编程 AI 出错、但题意严谨可评测的中文编程题。

题型：{family_title}
输入格式固定：{input_format}
输出格式固定：{output_format}

必须遵守：
1. 只生成题面，不生成测试用例，不生成答案代码。
2. 不要改变输入输出 JSON schema。
3. 题面要原创，不要复制搜索结果原文。
4. 必须突出边界条件、非法输入和 AI 容易误判点。
5. 返回严格 JSON，不要 Markdown 代码块。

容易出错的点：
{trap_text}

搜索到的相关素材：
{source_text}

返回 JSON 格式：
{{
  "title": "中文题目标题",
  "statement": "完整中文题面，包含任务描述和判定规则",
  "tags": ["tag1", "tag2"]
}}
"""


def fallback_variant(title: str, statement: str, tags: list[str]) -> ProblemVariant:
    return ProblemVariant(id="ai-fallback", title=title, statement=statement, tags=tags)

