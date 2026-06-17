from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse

router = APIRouter(prefix = "/notifications", tags = ["notifications"])

@router.get("/me", response_model = list[NotificationResponse])
def get_my_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Notification).filter(
        Notification.recipient_id == current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()

@router.patch("/{notification_id}/read", response_model = NotificationResponse)
def mark_as_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id # ensures that users can mark only their own notifications as read
    ).first()
    if not notification:
        raise HTTPException(status_code = 404, detail = "Notification not found.")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification