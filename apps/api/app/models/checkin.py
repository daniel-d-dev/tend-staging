from sqlalchemy import Integer, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime, timezone
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class CheckIn(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable = False, index = True)
    checkin_date: Mapped[date] = mapped_column(Date, nullable = False)
    prompt_question: Mapped[str] = mapped_column(Text, nullable = False)
    prompt_response: Mapped[str] = mapped_column(Text, nullable = False)
    journal_text: Mapped[str | None] = mapped_column(Text, nullable = True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable = True)
    step_count: Mapped[int | None] = mapped_column(Integer, nullable = True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable = True) # null until the NLP scores it when its submitted
    band_label: Mapped[str | None] = mapped_column(Text, nullable = True) # the distress band assigned by the scoring pipeline. It is for internal use only and is not returned to clients
    audio_emotion_score: Mapped[float | None] = mapped_column(Float, nullable = True) # populated by audeering from raw voice audio, it is null for checkins that only use text
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), default = utc_now)