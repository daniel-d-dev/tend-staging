from sqlalchemy import Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable = False, index = True)
    author_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable = True)
    content: Mapped[str] = mapped_column(String, nullable = False)
    author_type: Mapped[str] = mapped_column(String, nullable = False)
    parent_post_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("posts.id"), nullable = True)
    mode: Mapped[str | None] = mapped_column(String, nullable = True) # only set for coordinator posts, either urgent, supportive, connective or activity, null for real user posts. Lets the urgent cooldown in coordinator.py tell an urgent post apart from a routine one
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), default = (utc_now))

class Reaction(Base):
    __tablename__ = "reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), nullable = False, index = True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable = False)
    emoji: Mapped[str] = mapped_column(String, nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), default = (utc_now))

    __table_args__ = (UniqueConstraint("post_id", "user_id", "emoji"),)