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
        word = data.word.strip().lower()
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

    total_members = db.query(GroupMember).filter(GroupMember.group_id == group_id).count()
    response_count = len(checks)
    revealed = response_count >= 3 and response_count / total_members >= 0.6 # only revealed once at least 3 members have responded and 60% participation is reached

    if not revealed:
        return TemperatureAggregateResponse(
            week_start = week_start,
            revealed = False,
            response_count = response_count,
            words = None
        )

    word_counts = {}
    for c in checks:
        word_counts[c.word] = word_counts.get(c.word, 0) + 1

    return TemperatureAggregateResponse(
        week_start = week_start,
        revealed = True,
        response_count = response_count,
        words = word_counts
    )
