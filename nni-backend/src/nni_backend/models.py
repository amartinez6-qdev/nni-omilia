from typing import Literal

from pydantic import BaseModel, Field


class InterpretationResponse(BaseModel):
    transcript: str = Field(min_length=1)
    interpretation: str = Field(pattern=r"^\d+$")
    valid_greek_phone: bool


class HealthResponse(BaseModel):
    status: Literal["ok"]
