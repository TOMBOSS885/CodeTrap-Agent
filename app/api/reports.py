from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

from app.database import db

router = APIRouter()


def get_report_paths(report_id: str) -> tuple[Path, Path]:
    with db() as conn:
        row = conn.execute("select markdown_path, html_path from reports where id = ?", (report_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="report not found")
    return Path(row[0]), Path(row[1])


@router.get("/reports/{report_id}", response_class=HTMLResponse)
def view_report(report_id: str):
    _, html_path = get_report_paths(report_id)
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="report file missing")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@router.get("/reports/{report_id}/download")
def download_report(report_id: str):
    md_path, _ = get_report_paths(report_id)
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="report file missing")
    return FileResponse(md_path, media_type="text/markdown", filename=f"{report_id}.md")


@router.get("/reports/{report_id}/raw", response_class=PlainTextResponse)
def raw_report(report_id: str):
    md_path, _ = get_report_paths(report_id)
    return PlainTextResponse(md_path.read_text(encoding="utf-8"))

