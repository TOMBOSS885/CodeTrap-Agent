from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import REPORT_DIR, SANDBOX_BACKEND, SANDBOX_DOCKER_IMAGE, UPLOAD_DIR
from app.database import db
from codetrap.core.registry import registry
from codetrap.core.testcase import TestCase
from codetrap.judge.runner import JudgeRunner
from codetrap.judge.sandbox import create_sandbox
from codetrap.reports.html_report import render_html_report
from codetrap.reports.markdown_report import render_markdown_report

router = APIRouter()


@router.post("/judge/{family_id}")
async def judge_solution(
    family_id: str,
    level: str = Form("basic"),
    count: int = Form(5),
    cases_json: str | None = Form(None),
    file: UploadFile = File(...),
):
    try:
        family = registry.get(family_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    run_id = uuid.uuid4().hex
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = ".py" if not file.filename or not file.filename.endswith(".py") else ""
    solution_path = UPLOAD_DIR / f"{run_id}_{file.filename or 'solution'}{suffix}"
    solution_path.write_bytes(await file.read())
    if cases_json:
        raw_cases = json.loads(cases_json)
        cases = [TestCase.model_validate(item) for item in raw_cases]
    else:
        cases = family.generate_cases(level, count)
    sandbox = create_sandbox(SANDBOX_BACKEND, SANDBOX_DOCKER_IMAGE)
    result = JudgeRunner(sandbox=sandbox).judge(family, str(solution_path), cases)
    report_id = uuid.uuid4().hex
    md = render_markdown_report(family, file.filename or solution_path.name, result)
    html = render_html_report(family, file.filename or solution_path.name, result)
    md_path = REPORT_DIR / f"{report_id}.md"
    html_path = REPORT_DIR / f"{report_id}.html"
    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    with db() as conn:
        conn.execute("insert into judge_runs (id, family_id, solution_name, passed, total_cases, passed_cases) values (?, ?, ?, ?, ?, ?)", (run_id, family_id, file.filename or "solution.py", int(result.passed), result.total_cases, result.passed_cases))
        conn.execute("insert into reports (id, judge_run_id, markdown_path, html_path) values (?, ?, ?, ?)", (report_id, run_id, str(md_path), str(html_path)))
    return {"report_id": report_id, "sandbox": getattr(sandbox, "backend_name", SANDBOX_BACKEND), "result": result.model_dump()}
