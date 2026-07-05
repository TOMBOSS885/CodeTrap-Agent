from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.config import LLM_API_BASE, LLM_API_KEY, LLM_MODEL, LLM_PROVIDER
from app.database import db
from app.repositories import list_problem_bundle_summaries, load_problem_bundle, save_problem_bundle
from app.schemas import GenerateCasesRequest
from codetrap.core.registry import registry
from codetrap.llm.client import LLMConfig, LLMProblemGenerator
from codetrap.search.web_search import search_related_problems

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


@router.get("/problems")
def list_problems(limit: int = 50):
    with db() as conn:
        return list_problem_bundle_summaries(conn, limit=min(max(limit, 1), 200))


@router.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    with db() as conn:
        bundle = load_problem_bundle(conn, problem_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="problem not found")
    return {"problem_id": problem_id, "problem": bundle.model_dump()}


@router.post("/families/{family_id}/problem")
def generate_problem(family_id: str, request: GenerateCasesRequest):
    try:
        family = registry.get(family_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    query = request.query or f"{family.title} common pitfalls algorithm problem AI fails edge cases"
    if request.search_online:
        sources, search_status = search_related_problems(query)
    else:
        sources, search_status = [], "online_search_disabled"
    ai_variant = None
    generation_status = "local_variant"
    if request.use_ai:
        generator = LLMProblemGenerator(LLMConfig(provider=LLM_PROVIDER, api_key=LLM_API_KEY, model=LLM_MODEL, api_base=LLM_API_BASE))
        ai_variant, generation_status = generator.generate_variant(family, sources)
    bundle = family.generate_problem_bundle(request.level, request.count, sources, query, search_status, variant=ai_variant, generation_status=generation_status)
    run_id = uuid.uuid4().hex
    problem_id = uuid.uuid4().hex
    with db() as conn:
        conn.execute("insert into problem_runs (id, family_id, level, count) values (?, ?, ?, ?)", (run_id, family_id, request.level, request.count))
        save_problem_bundle(conn, problem_id, run_id, bundle)
    return {"run_id": run_id, "problem_id": problem_id, "problem": bundle.model_dump()}
