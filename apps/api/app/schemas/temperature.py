from pydantic import BaseModel, Field
from datetime import date

class TemperatureCheckCreate(BaseModel):
    group_id: int
    rating: int = Field(ge = 1, le = 5)

class TemperatureCheckResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    week_start: date
    rating: int
    
    model_config = { "from_attributes": True }

class TemperatureAggregateResponse(BaseModel):
    week_start: date
    average_rating: float | None
    response_count: int

