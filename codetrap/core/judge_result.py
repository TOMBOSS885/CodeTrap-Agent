from __future__ import annotations

from pydantic import BaseModel, Field


class FailedCase(BaseModel):
    case_id: str
    name: str
    input_data: dict
    expected_output: object
    actual_output: object | None = None
    error_type: str
    error_message: str | None = None
    trap_reason: str
    tags: list[str] = Field(default_factory=list)


class JudgeResult(BaseModel):
    passed: bool
    total_cases: int
    passed_cases: int
    failed_cases: list[FailedCase] = Field(default_factory=list)
    runtime_ms: int
    memory_mb: float | None = None
    error_type: str | None = None
    weakness_summary: str = ""

