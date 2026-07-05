from __future__ import annotations

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    id: str
    name: str
    input_data: dict
    expected_output: object | None = None
    trap_reason: str
    difficulty: str = "basic"
    tags: list[str] = Field(default_factory=list)
    is_hidden: bool = False

