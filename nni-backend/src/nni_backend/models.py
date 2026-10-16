from typing import Literal

from pydantic import BaseModel, Field


class InterpretationItem(BaseModel):
    number: str = Field(pattern=r"^\d+$")
    valid_greek_phone: bool


class InterpretationResponse(BaseModel):
    transcript: str = Field(min_length=1)
    interpretations: list[InterpretationItem] = Field(min_length=1)


class HealthResponse(BaseModel):
    status: Literal["ok"]
