from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from app.config import DATA_DIR, DB_PATH, REPORT_DIR, UPLOAD_DIR


def init_db() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("create table if not exists problem_runs (id text primary key, family_id text, level text, count integer, created_at text default current_timestamp)")
        conn.execute("create table if not exists judge_runs (id text primary key, family_id text, solution_name text, passed integer, total_cases integer, passed_cases integer, created_at text default current_timestamp)")
        conn.execute("create table if not exists reports (id text primary key, judge_run_id text, markdown_path text, html_path text, created_at text default current_timestamp)")


@contextmanager
def db():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

