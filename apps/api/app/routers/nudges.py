from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.nudge import NudgeFlag

router = APIRouter(prefix = "/nudges", tags = ["nudges"])

@router.get("/me")
def get_my_nudges(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(NudgeFlag).filter(
        NudgeFlag.user_id == current_user.id
    ).order_by(
        NudgeFlag.triggered_at.desc()
    ).all()