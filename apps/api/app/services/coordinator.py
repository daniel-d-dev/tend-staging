from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.group import GroupMember
from app.models.group import Group
from app.models.checkin import CheckIn
from app.models.nudge import NudgeFlag
from app.models.temperature import TemperatureCheck
from app.models.feed import Post
from app.core.database import SessionLocal
from app.core.message_generator import generate_message

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

DISTRESS_BANDS = {"Moderate difficulty", "Significant difficulty", "High distress"}

def select_mode(signals: dict) -> str | None:
    if signals["has_high_distress"]:
        return "urgent"
    if signals["avg_sentiment"] is None:
        return None
    if signals["has_recent_flag"]:
        return "connective"
    avg_sentiment = signals["avg_sentiment"]
    members_with_band_labels = len(signals["band_labels"])
    distress_count = sum(1 for b in signals["band_labels"] if b in DISTRESS_BANDS) # count members in the bands that are concerning
    majority_distressed = members_with_band_labels > 0 and distress_count >= members_with_band_labels / 2 # true if half or more of active members are in distress bands
    if avg_sentiment < 0.15 and distress_count == 0:
        return "activity"
    if avg_sentiment > 0.35 or majority_distressed:
        return "supportive"
    return "connective"

def select_activity_category(signals: dict, last_category: str | None) -> str:
    day = datetime.now(timezone.utc).weekday() # 0 is Monday and 6 is Sunday
    if day in (0, 6):
        category = "reflective"
    elif day == 5:
        category = "physical"
    else:
        category = "social"
    if signals["avg_sentiment"] is not None and signals["avg_sentiment"] > 0.30 and category == "physical":
        category = "social" # physical can help mild low mood but we avoid it when the group is genuinely struggling
    return category

def run_coordinator(group_id: int, db: Session) -> None:
    last_post = db.query(Post).filter(
        Post.group_id == group_id,
        Post.author_type == "agent"
    ).order_by(Post.created_at.desc()).first()

    signals = read_group_signals(group_id, db)

    if last_post:
        hours_since = (datetime.now(timezone.utc) - last_post.created_at).total_seconds() / 3600
        if signals["has_high_distress"]:
            if hours_since < 12:
                return # urgent cooldown of 12 hours
        elif hours_since < 48:
            return # standard cooldown of 48 hours
            
    mode = select_mode(signals)
    if mode is None:
        return
    
    category = select_activity_category(signals, None) if mode == "activity" else None
    last_post_summary = last_post.content if last_post else None
    message = generate_message(mode, category, signals, last_post_summary)

    post = Post(
        group_id = group_id,
        author_id = None,
        content = message,
        author_type = "agent"
    )
    db.add(post)
    db.commit()

def coordinator_job():
    with SessionLocal() as db:
        groups = db.query(Group).all()
        for group in groups:
            run_coordinator(group.id, db)