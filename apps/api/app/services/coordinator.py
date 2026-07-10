from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.group import GroupMember
from app.models.checkin import CheckIn
from app.models.nudge import NudgeFlag
from app.models.temperature import TemperatureCheck
from app.models.feed import Post
from app.core.database import SessionLocal

def read_group_signals(group_id: int, db: Session) -> dict:
    cutoff = datetime.now(timezone.utc).date() - timedelta(days = 3) # they're active if they've checked in within the past three days
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).all()
    member_ids = [m.user_id for m in members]
    sentiment_scores = []
    band_labels = []
    for user_id in member_ids:
        checkin = db.query(CheckIn).filter(
            CheckIn.user_id == user_id,
            CheckIn.checkin_date >= cutoff
        ).order_by(CheckIn.checkin_date.desc()).first()
        if checkin:
            if checkin.sentiment_score is not None:
                sentiment_scores.append(checkin.sentiment_score)
            if checkin.band_label is not None:
                band_labels.append(checkin.band_label)
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else None

    today = datetime.now(timezone.utc).date()
    week_start = today - timedelta(days = today.weekday()) # rewind to Monday of current week
    temperature_words = [tc.word for tc in db.query(TemperatureCheck).filter(
        TemperatureCheck.group_id == group_id,
        TemperatureCheck.week_start == week_start
    ).all()]
    recent_flags = db.query(NudgeFlag).filter(
        NudgeFlag.user_id.in_(member_ids),
        NudgeFlag.triggered_at >= datetime.now(timezone.utc) - timedelta(days = 3)
    ).all()
    has_recent_flag = len(recent_flags) > 0
    has_high_distress = any(f.trigger_rule == "band_high_distress_1d" for f in recent_flags) # overrides cooldown, urgent response only
    return {
        "member_count": len(members),
        "active_count": len(sentiment_scores),
        "avg_sentiment": avg_sentiment,
        "band_labels": band_labels,
        "temperature_words": temperature_words,
        "has_recent_flag": has_recent_flag,
        "has_high_distress": has_high_distress
    }