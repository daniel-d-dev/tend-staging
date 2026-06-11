from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.checkin import CheckIn
from app.models.nudge import NudgeFlag
from app.core.baseline import get_baseline

def is_on_cooldown(user_id: int, db: Session) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(days = 3)
    recent = db.query(NudgeFlag).filter(
        NudgeFlag.user_id == user_id,
        NudgeFlag.triggered_at >= cutoff
    ).first()
    if recent is not None:
        return True
    else:
        return False

def create_nudge_flag(user_id: int, trigger_rule: str, db: Session) -> NudgeFlag:
    flag = NudgeFlag(user_id = user_id, trigger_rule = trigger_rule)
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag

def run_inference(user_id: int, db: Session) -> NudgeFlag | None:
    baseline = get_baseline(user_id, db)

    if not baseline["sufficient_data"]:
        return None # there is less than 7 checkins meaning there is not enough history to compare against
    
    if baseline["sentiment_mean"] is None:
        return None # there are checkins but none have been scored yet
    
    if is_on_cooldown(user_id, db):
        return None # a nudge has been sent already in the past 3 days

    avg_sentiment = baseline["sentiment_mean"]
    recent = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user_id)
        .order_by(CheckIn.checkin_date.desc())
        .limit(3)
        .all()
    )

    if len(recent) >= 2:
        last_two = recent[:2]
        if all(c.sentiment_score < avg_sentiment - 0.5 for c in last_two): # 0.5 is quite a drop so it triggers faster
            return create_nudge_flag(user_id, "sentiment_sustained_2d", db)
        
    if len(recent) >= 3:
        if all(c.sentiment_score < avg_sentiment - 0.3 for c in recent): # 0.3 is less of a drop so it's sustained longer
            return create_nudge_flag(user_id, "sentiment_sustained_3d", db)
    
    if len(recent) >= 1:
        latest = recent[0]
        sentiment_low = latest.sentiment_score < avg_sentiment - 0.3
        sleep_low = latest.sleep_hours is not None and latest.sleep_hours < baseline["sleep_mean"]
        steps_low = latest.step_count is not None and latest.step_count < baseline["steps_mean"]
        if sentiment_low and (sleep_low or steps_low):
            return create_nudge_flag(user_id, "sentiment_convergent", db)
        
    if len(recent) == 0 or (recent and (datetime.now(timezone.utc).date() - recent[0].checkin_date).days >= 3): # no checkins or the last one was more than 3 days ago
        return create_nudge_flag(user_id, "ghost_checkin_3d", db)
    
    return None