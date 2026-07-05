from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.database import db
from app.schemas import GenerateCasesRequest
from codetrap.core.registry import registry

router = APIRouter()


@router.get("/families")
def list_families():
    return [
        {
            "family_id": family.family_id,
            "title": family.title,
            "description": family.description,
            "difficulty": family.difficulty,
            "tags": family.tags,
        }
        for family in registry.all()
    ]


@router.get("/families/{family_id}")
def get_family(family_id: str):
    try:
        family = registry.get(family_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    mutants = family.generate_mutants()
    return {
        "family_id": family.family_id,
        "title": family.title,
        "description": family.description,
        "input_format": family.input_format,
        "output_format": family.output_format,
        "difficulty": family.difficulty,
        "tags": family.tags,
        "mutants": [
            {
                "id": mutant.id,
                "title": mutant.title,
                "description": mutant.description,
                "code": mutant.code,
            }
            for mutant in mutants
        ],
    }


@router.post("/families/{family_id}/cases")
def generate_cases(family_id: str, request: GenerateCasesRequest):
    try:
        family = registry.get(family_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    cases = family.generate_cases(request.level, request.count)
    run_id = uuid.uuid4().hex
    with db() as conn:
        conn.execute("insert into problem_runs (id, family_id, level, count) values (?, ?, ?, ?)", (run_id, family_id, request.level, request.count))
    return {"run_id": run_id, "cases": [case.model_dump() for case in cases]}
