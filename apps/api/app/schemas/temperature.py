from pydantic import BaseModel, Field, field_validator
from datetime import date

def reject_blank(v: str) -> str: # min_length alone won't catch whitespace-only input even though it is still technically non-empty, so this backs it up
    if not v.strip():
        raise ValueError("word cannot be empty or just whitespace")
    return v

class TemperatureCheckCreate(BaseModel):
    group_id: int
    word: str = Field(min_length = 1)

    validate_word = field_validator("word")(reject_blank)

class TemperatureCheckResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    week_start: date
    word: str
    
    model_config = { "from_attributes": True }

class TemperatureAggregateResponse(BaseModel):
    week_start: date
    revealed: bool
    response_count: int
    words: dict[str, int] | None