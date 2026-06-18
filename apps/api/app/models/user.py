from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    email: Mapped[str] = mapped_column(String, unique = True, nullable = False, index = True)
    hashed_password: Mapped[str] = mapped_column(String, nullable = False)
    display_name: Mapped[str] = mapped_column(String, nullable = False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = utc_now
    )
    push_token: Mapped[str | None] = mapped_column(String, nullable = True)