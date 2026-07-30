from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime

# min_length alone won't catch whitespace-only input even though it is still technically non-empty, so this backs it up
def reject_blank(v: str | None) -> str | None:
    if v is not None and not v.strip():
        raise ValueError("prompt_response cannot be empty or just whitespace")
    return v

class CheckInCreate(BaseModel):
    prompt_question: str # client sends this until the prompt bank route exists
    prompt_response: str = Field(min_length = 1)
    journal_text: str | None = None
    sleep_hours: float | None = Field(default = None, ge = 0, le = 24)
    step_count: int | None = Field(default = None, ge = 0)
    audio_emotion_score: float | None = None

    validate_prompt_response = field_validator("prompt_response")(reject_blank)

class CheckInUpdate(BaseModel):
    prompt_response: str | None = Field(default = None, min_length = 1)
    journal_text: str | None = None
    sleep_hours: float | None = Field(default = None, ge = 0, le = 24)
    step_count: int | None = Field(default = None, ge = 0)
    audio_emotion_score: float | None = None

    validate_prompt_response = field_validator("prompt_response")(reject_blank)

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