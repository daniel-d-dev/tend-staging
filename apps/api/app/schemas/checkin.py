from pydantic import BaseModel
from datetime import date, datetime

class CheckInCreate(BaseModel):
    prompt_question: str # client sends this until the prompt bank route exists
    prompt_response: str
    journal_text: str | None = None
    sleep_hours: float | None = None
    step_count: int | None = None

class CheckInUpdate(BaseModel):
    prompt_response: str | None = None
    journal_text: str | None = None
    sleep_hours: float | None = None
    step_count: int | None = None

class CheckInResponse(BaseModel):
    id: int
    user_id: int
    checkin_date: date
    prompt_question: str
    prompt_response: str
    journal_text: str | None
    sleep_hours: float | None
    step_count: int | None
    sentiment_score: float | None
    created_at: datetime

    model_config = {'from_attributes': True}