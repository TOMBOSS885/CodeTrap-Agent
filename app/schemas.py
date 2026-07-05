from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateCasesRequest(BaseModel):
    level: str = Field(default="basic", pattern="^(basic|edge|adversarial)$")
    count: int = Field(default=5, ge=1, le=50)
    search_online: bool = True
    query: str | None = None


class JudgeResponse(BaseModel):
    report_id: str
    result: dict
