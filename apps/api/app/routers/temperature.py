from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.core.database import get_db
from app.models.temperature import TemperatureCheck
from app.models.group import GroupMember
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.temperature import TemperatureCheckCreate, TemperatureCheckResponse, TemperatureAggregateResponse

router = APIRouter(prefix = "/temperature", tags = ["temperature"])

@router.post("/", response_model = TemperatureCheckResponse)
def submit_temperature(
    data: TemperatureCheckCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == data.group_id,
        GroupMember.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(status_code = 403, detail = "You are not a member of this group.")
    
    today = date.today()
    week_start = today - timedelta(days = today.weekday()) # monday of the current week

    existing = db.query(TemperatureCheck).filter(
        TemperatureCheck.group_id == data.group_id,
        TemperatureCheck.user_id == current_user.id,
        TemperatureCheck.week_start == week_start
    ).first()

    if existing:
        raise HTTPException(status_code = 400, detail = "You have already submitted a temperature check for this group this week.")
    
    check = TemperatureCheck(
        group_id = data.group_id,
        user_id = current_user.id,
        week_start = week_start,
        rating = data.rating
    )

    db.add(check)
    db.commit()
    db.refresh(check)
    return check

@router.get("/mine", response_model = list[TemperatureCheckResponse])
def get_my_temperature_checks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    week_start = today - timedelta(days = today.weekday())
    checks = db.query(TemperatureCheck).filter(
        TemperatureCheck.user_id == current_user.id,
        TemperatureCheck.week_start == week_start
    ).all()
    return checks

@router.get("/group/{group_id}", response_model = TemperatureAggregateResponse)
def get_group_temperature(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(status_code = 403, detail = "You are not a member of this group.")
    
    today = date.today()
    week_start = today - timedelta(days = today.weekday())

    checks = db.query(TemperatureCheck).filter(
        TemperatureCheck.group_id == group_id,
        TemperatureCheck.week_start == week_start
    ).all()

    if not checks: # no submissions yet this week is valid so it is handled like this, not with an error
        return TemperatureAggregateResponse(
            week_start = week_start,
            average_rating = None,
            response_count = 0
        )
    
    average = sum(c.rating for c in checks) / len(checks)

    return TemperatureAggregateResponse(
            week_start = week_start,
            average_rating = average,
            response_count = len(checks)
        )