from __future__ import annotations

from codetrap.core.judge_result import JudgeResult
from codetrap.core.problem import ProblemFamily
from codetrap.utils.json_utils import to_pretty_json


def render_markdown_report(family: ProblemFamily, solution_name: str, result: JudgeResult) -> str:
    rate = 0 if result.total_cases == 0 else result.passed_cases / result.total_cases * 100
    lines = [
        "# CodeTrap-Agent 评测报告",
        "",
        f"- 题型：{family.title} (`{family.family_id}`)",
        f"- 候选文件：`{solution_name}`",
        f"- 测试用例总数：{result.total_cases}",
        f"- 通过用例数：{result.passed_cases}",
        f"- 失败用例数：{len(result.failed_cases)}",
        f"- 通过率：{rate:.1f}%",
        f"- 运行耗时：{result.runtime_ms} ms",
        "",
        "## 弱点总结",
        "",
        result.weakness_summary,
        "",
        "## 失败用例",
        "",
    ]
    if not result.failed_cases:
        lines.append("本次评测没有失败用例。")
    for failed in result.failed_cases:
        lines.extend([
            f"### {failed.name} (`{failed.case_id}`)",
            "",
            f"- 错误类型：`{failed.error_type}`",
            f"- 陷阱原因：{failed.trap_reason}",
            "",
            "**输入**",
            "```json",
            to_pretty_json(failed.input_data),
            "```",
            "**期望输出**",
            "```json",
            to_pretty_json(failed.expected_output),
            "```",
            "**实际输出**",
            "```json",
            to_pretty_json(failed.actual_output),
            "```",
        ])
    lines.extend(["", "## 改进建议", "", "请重点检查失败用例对应的陷阱类别，并针对输入校验、边界条件、初始状态和操作语义补充处理逻辑。"])
    return "\n".join(lines)
