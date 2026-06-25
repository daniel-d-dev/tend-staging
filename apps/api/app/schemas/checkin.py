from pydantic import BaseModel
from datetime import date, datetime

class CheckInCreate(BaseModel):
    prompt_question: str # client sends this until the prompt bank route exists
    prompt_response: str
    journal_text: str | None = None
    sleep_hours: float | None = None
    step_count: int | None = None
    audio_emotion_score: float | None = None

class CheckInUpdate(BaseModel):
    prompt_response: str | None = None
    journal_text: str | None = None
    sleep_hours: float | None = None
    step_count: int | None = None
    audio_emotion_score: float | None = None

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
    audio_emotion_score: float | None # derived from voice audio by audeering. Audio is transcribed separately, so this is optional on submission and null for text-only check-ins

    model_config = {'from_attributes': True}