from fastapi.testclient import TestClient

from app.main import app
from codetrap.core.registry import registry
from codetrap.reports.html_report import render_html_report
from codetrap.reports.markdown_report import render_markdown_report
from codetrap.judge.runner import JudgeRunner


def test_markdown_report_generation():
    family = registry.get("graph_paths")
    result = JudgeRunner(timeout_sec=3).judge(family, "examples/wrong_solution_graph.py", family.generate_cases("edge", 1))
    report = render_markdown_report(family, "wrong_solution_graph.py", result)
    assert "CodeTrap-Agent 评测报告" in report
    assert "弱点总结" in report
    html = render_html_report(family, "wrong_solution_graph.py", result)
    assert "<section class=\"panel\">" in html
    assert "失败用例" in html


def test_health_api():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}


def test_family_detail_api_includes_mutants():
    client = TestClient(app)
    response = client.get("/api/families/graph_paths")
    assert response.status_code == 200
    data = response.json()
    assert data["family_id"] == "graph_paths"
    assert len(data["mutants"]) >= 3
