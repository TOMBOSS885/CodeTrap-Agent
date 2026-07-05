from __future__ import annotations

from pydantic import BaseModel, Field

from codetrap.core.testcase import TestCase


class SearchSource(BaseModel):
    title: str
    url: str
    snippet: str = ""


class ProblemBundle(BaseModel):
    family_id: str
    title: str
    statement: str
    input_format: str
    output_format: str
    difficulty: str
    tags: list[str] = Field(default_factory=list)
    cases: list[TestCase] = Field(default_factory=list)
    reference_answer: str
    sources: list[SearchSource] = Field(default_factory=list)
    search_query: str
    search_status: str = "offline_fallback"

