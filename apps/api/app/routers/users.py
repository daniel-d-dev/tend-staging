from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.user import PushTokenUpdate

router = APIRouter(prefix = "/users", tags = ["users"])

@router.post("/push-token")
def register_push_token(
    data: PushTokenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.push_token = data.token
    db.commit()
    return {"ok": True}