from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from app.config import DATA_DIR, DB_PATH, REPORT_DIR, UPLOAD_DIR


def init_db() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("pragma foreign_keys = on")
        conn.execute("create table if not exists problem_runs (id text primary key, family_id text, level text, count integer, created_at text default current_timestamp)")
        conn.execute("create table if not exists judge_runs (id text primary key, family_id text, solution_name text, passed integer, total_cases integer, passed_cases integer, created_at text default current_timestamp)")
        conn.execute("create table if not exists reports (id text primary key, judge_run_id text, markdown_path text, html_path text, created_at text default current_timestamp)")
        conn.execute(
            """
            create table if not exists problem_bundles (
                id text primary key,
                run_id text,
                family_id text not null,
                title text not null,
                statement text not null,
                input_format text not null,
                output_format text not null,
                difficulty text not null,
                tags_json text not null,
                reference_answer text not null,
                search_query text not null,
                search_status text not null,
                created_at text default current_timestamp,
                foreign key(run_id) references problem_runs(id)
            )
            """
        )
        conn.execute(
            """
            create table if not exists problem_cases (
                id text primary key,
                case_id text,
                problem_id text not null,
                case_order integer not null,
                name text not null,
                input_json text not null,
                expected_json text not null,
                trap_reason text not null,
                difficulty text not null,
                tags_json text not null,
                is_hidden integer not null default 0,
                foreign key(problem_id) references problem_bundles(id) on delete cascade
            )
            """
        )
        _ensure_column(conn, "problem_cases", "case_id", "text")
        conn.execute(
            """
            create table if not exists problem_sources (
                id integer primary key autoincrement,
                problem_id text not null,
                source_order integer not null,
                title text not null,
                url text not null,
                snippet text not null,
                foreign key(problem_id) references problem_bundles(id) on delete cascade
            )
            """
        )
        _ensure_column(conn, "judge_runs", "problem_id", "text")
        conn.execute("create index if not exists idx_problem_bundles_family on problem_bundles(family_id)")
        conn.execute("create index if not exists idx_problem_cases_problem on problem_cases(problem_id)")
        conn.execute("create index if not exists idx_judge_runs_problem on judge_runs(problem_id)")


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row[1] for row in conn.execute(f"pragma table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"alter table {table} add column {column} {definition}")


@contextmanager
def db():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("pragma foreign_keys = on")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
