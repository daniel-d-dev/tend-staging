from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    recipient_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable = False, index = True)
    nudge_flag_id: Mapped[int] = mapped_column(Integer, ForeignKey("nudge_flags.id"), nullable = False)
    message: Mapped[str] = mapped_column(String, nullable = False)
    is_read: Mapped[bool] = mapped_column(Boolean, default = False, nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), default = utc_now)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone = True), nullable = True)