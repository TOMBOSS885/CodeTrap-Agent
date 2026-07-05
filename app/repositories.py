from __future__ import annotations

import json

from codetrap.core.problem_bundle import ProblemBundle, SearchSource
from codetrap.core.testcase import TestCase


def save_problem_bundle(conn, problem_id: str, run_id: str, bundle: ProblemBundle) -> None:
    conn.execute(
        """
        insert into problem_bundles (
            id, run_id, family_id, title, statement, input_format, output_format,
            difficulty, tags_json, reference_answer, search_query, search_status
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            problem_id,
            run_id,
            bundle.family_id,
            bundle.title,
            bundle.statement,
            bundle.input_format,
            bundle.output_format,
            bundle.difficulty,
            json.dumps(bundle.tags, ensure_ascii=False),
            bundle.reference_answer,
            bundle.search_query,
            bundle.search_status,
        ),
    )
    for index, case in enumerate(bundle.cases):
        case_row_id = f"{problem_id}:{index}:{case.id}"
        conn.execute(
            """
            insert into problem_cases (
                id, case_id, problem_id, case_order, name, input_json, expected_json,
                trap_reason, difficulty, tags_json, is_hidden
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_row_id,
                case.id,
                problem_id,
                index,
                case.name,
                json.dumps(case.input_data, ensure_ascii=False),
                json.dumps(case.expected_output, ensure_ascii=False),
                case.trap_reason,
                case.difficulty,
                json.dumps(case.tags, ensure_ascii=False),
                int(case.is_hidden),
            ),
        )
    for index, source in enumerate(bundle.sources):
        conn.execute(
            """
            insert into problem_sources (problem_id, source_order, title, url, snippet)
            values (?, ?, ?, ?, ?)
            """,
            (problem_id, index, source.title, source.url, source.snippet),
        )


def load_problem_bundle(conn, problem_id: str) -> ProblemBundle | None:
    row = conn.execute(
        """
        select family_id, title, statement, input_format, output_format, difficulty,
               tags_json, reference_answer, search_query, search_status
        from problem_bundles where id = ?
        """,
        (problem_id,),
    ).fetchone()
    if row is None:
        return None
    case_rows = conn.execute(
        """
        select coalesce(case_id, id), name, input_json, expected_json, trap_reason, difficulty, tags_json, is_hidden
        from problem_cases where problem_id = ? order by case_order
        """,
        (problem_id,),
    ).fetchall()
    source_rows = conn.execute(
        """
        select title, url, snippet from problem_sources
        where problem_id = ? order by source_order
        """,
        (problem_id,),
    ).fetchall()
    return ProblemBundle(
        family_id=row[0],
        title=row[1],
        statement=row[2],
        input_format=row[3],
        output_format=row[4],
        difficulty=row[5],
        tags=json.loads(row[6]),
        reference_answer=row[7],
        search_query=row[8],
        search_status=row[9],
        cases=[
            TestCase(
                id=case[0],
                name=case[1],
                input_data=json.loads(case[2]),
                expected_output=json.loads(case[3]),
                trap_reason=case[4],
                difficulty=case[5],
                tags=json.loads(case[6]),
                is_hidden=bool(case[7]),
            )
            for case in case_rows
        ],
        sources=[
            SearchSource(title=source[0], url=source[1], snippet=source[2])
            for source in source_rows
        ],
    )


def list_problem_bundle_summaries(conn, limit: int = 50) -> list[dict]:
    rows = conn.execute(
        """
        select pb.id, pb.family_id, pb.title, pb.difficulty, pb.search_status,
               pb.created_at, count(pc.id) as case_count
        from problem_bundles pb
        left join problem_cases pc on pc.problem_id = pb.id
        group by pb.id
        order by pb.created_at desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "problem_id": row[0],
            "family_id": row[1],
            "title": row[2],
            "difficulty": row[3],
            "search_status": row[4],
            "created_at": row[5],
            "case_count": row[6],
        }
        for row in rows
    ]
