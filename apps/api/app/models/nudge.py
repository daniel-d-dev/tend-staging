from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class NudgeFlag(Base):
    __tablename__ = "nudge_flags"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable = False, index = True)
    trigger_rule: Mapped[str] = mapped_column(String, nullable = False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), default = utc_now)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone = True), nullable = True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone = True), nullable = True)