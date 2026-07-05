from __future__ import annotations

import html

from codetrap.core.judge_result import JudgeResult
from codetrap.core.problem import ProblemFamily
from codetrap.utils.json_utils import to_pretty_json


def render_html_report(family: ProblemFamily, solution_name: str, result: JudgeResult) -> str:
    rate = 0 if result.total_cases == 0 else result.passed_cases / result.total_cases * 100
    status_class = "passed" if result.passed else "failed"
    failed_rows = []
    for failed in result.failed_cases:
        failed_rows.append(
            f"""
            <article class="case">
              <div class="case-head">
                <h3>{html.escape(failed.name)}</h3>
                <span>{html.escape(failed.error_type)}</span>
              </div>
              <p>{html.escape(failed.trap_reason)}</p>
              <div class="grid">
                <div><h4>Input</h4><pre>{html.escape(to_pretty_json(failed.input_data))}</pre></div>
                <div><h4>Expected</h4><pre>{html.escape(to_pretty_json(failed.expected_output))}</pre></div>
                <div><h4>Actual</h4><pre>{html.escape(to_pretty_json(failed.actual_output))}</pre></div>
              </div>
            </article>
            """
        )
    failed_html = "\n".join(failed_rows) if failed_rows else '<p class="empty">No failed cases in this run.</p>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CodeTrap Report</title>
  <style>
    :root {{ --ink:#172026; --muted:#66737f; --line:#d8dee4; --bg:#f6f7f9; --panel:#fff; --ok:#047857; --bad:#b42318; --accent:#0f766e; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; color:var(--ink); background:var(--bg); line-height:1.5; }}
    header {{ background:var(--panel); border-bottom:1px solid var(--line); padding:28px 36px 20px; }}
    main {{ max-width:1120px; margin:0 auto; padding:24px; }}
    h1 {{ margin:0 0 6px; font-size:30px; letter-spacing:0; }}
    h2 {{ margin:26px 0 12px; font-size:20px; }}
    h3 {{ margin:0; font-size:17px; }}
    h4 {{ margin:0 0 8px; font-size:13px; color:var(--muted); text-transform:uppercase; }}
    p {{ margin:0; color:var(--muted); }}
    .summary {{ display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:12px; margin-top:18px; }}
    .metric, .panel, .case {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .metric strong {{ display:block; font-size:24px; }}
    .metric span {{ color:var(--muted); font-size:13px; }}
    .badge {{ display:inline-flex; padding:4px 10px; border-radius:999px; color:#fff; font-weight:700; font-size:13px; background:var(--bad); }}
    .badge.passed {{ background:var(--ok); }}
    .case {{ margin-bottom:14px; }}
    .case-head {{ display:flex; justify-content:space-between; gap:12px; align-items:center; margin-bottom:8px; }}
    .case-head span {{ color:var(--bad); font-weight:700; }}
    .grid {{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:12px; margin-top:12px; }}
    pre {{ margin:0; background:#101820; color:#e9f5f2; border-radius:6px; padding:12px; overflow:auto; min-height:88px; }}
    .empty {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    @media (max-width: 820px) {{ .summary, .grid {{ grid-template-columns:1fr; }} header {{ padding:22px; }} main {{ padding:14px; }} }}
  </style>
</head>
<body>
  <header>
    <span class="badge {status_class}">{'PASSED' if result.passed else 'FAILED'}</span>
    <h1>CodeTrap-Agent Evaluation Report</h1>
    <p>{html.escape(family.title)} · {html.escape(family.family_id)} · {html.escape(solution_name)}</p>
    <div class="summary">
      <div class="metric"><strong>{result.total_cases}</strong><span>Total cases</span></div>
      <div class="metric"><strong>{result.passed_cases}</strong><span>Passed cases</span></div>
      <div class="metric"><strong>{len(result.failed_cases)}</strong><span>Failed cases</span></div>
      <div class="metric"><strong>{rate:.1f}%</strong><span>Pass rate</span></div>
    </div>
  </header>
  <main>
    <section class="panel">
      <h2>Weakness Summary</h2>
      <p>{html.escape(result.weakness_summary)}</p>
    </section>
    <h2>Failed Cases</h2>
    {failed_html}
    <section class="panel">
      <h2>Improvement Advice</h2>
      <p>Review the failed trap categories and add targeted handling for validation, boundary cases, state initialization, and operation semantics.</p>
    </section>
  </main>
</body>
</html>"""
