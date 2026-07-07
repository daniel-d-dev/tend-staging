from sqlalchemy import Integer, DateTime, Date, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone, date
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class TemperatureCheck(Base):
    __tablename__ = "temperature_checks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable = False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable = False)
    week_start: Mapped[date] = mapped_column(Date, nullable = False)
    word: Mapped[int] = mapped_column(Text, nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), default = utc_now)

    __table_args__ = (UniqueConstraint("group_id", "user_id", "week_start"),) # one rating per user per group per week

    