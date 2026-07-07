from pydantic import BaseModel
from datetime import date

class TemperatureCheckCreate(BaseModel):
    group_id: int
    word: str

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