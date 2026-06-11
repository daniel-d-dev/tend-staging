from sqlalchemy import Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    name: Mapped[str] = mapped_column(String, nullable = False)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), default = utc_now)

class GroupMember(Base):
    __tablename__ = "group_members"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable = False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable = False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), default = utc_now)

    __table_args__ = (UniqueConstraint("group_id", "user_id"),) # prevents the same same user being added to the same group twice. The trailing comma makes this a tuple and is required by SQLalchemy