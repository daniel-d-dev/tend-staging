from sqlalchemy import Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
import secrets, string
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

def generate_join_code():
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    name: Mapped[str] = mapped_column(String, nullable = False)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), default = utc_now)
    join_code: Mapped[str] = mapped_column(String, nullable = False, unique = True, index = True, default = generate_join_code)

class GroupMember(Base):
    __tablename__ = "group_members"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, index = True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable = False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable = False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone = True), default = utc_now)

    __table_args__ = (UniqueConstraint("group_id", "user_id"),) # prevents the same user being added to the same group twice. The trailing comma makes this a tuple and is required by SQLalchemy