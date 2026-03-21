from pydantic import BaseModel, Field
from enum import StrEnum, IntEnum


class FilterOperand(StrEnum):
    EQUAL = "equal"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    CONTAINS = "contains"
    IN = "in"

class Strength(IntEnum):
    SOFT = 1
    MID = 2
    HARD = 3

class Filter(BaseModel):
    field: str = Field(..., description="Field name")
    operand: FilterOperand = Field(..., description="Operand type")
    value: str = Field(..., description="Field value")
    strength: Strength = Field(..., description="Filter strength")
    extraction_context: str = Field(..., description="Context in text where filter is extracted from")

class ModelOutput(BaseModel):
    filters: list[Filter] = Field(default_factory=list, description="List of filters")
    extra_info: str = Field(..., description="Descriptive subjective information to be embedded")