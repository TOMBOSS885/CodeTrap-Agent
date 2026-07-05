from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReportRecord:
    id: str
    judge_run_id: str
    markdown_path: str
    html_path: str

