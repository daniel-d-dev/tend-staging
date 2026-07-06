from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.checkin import CheckIn
from app.models.nudge import NudgeFlag
from app.core.baseline import get_baseline

AUDIO_DISTRESS_THRESHOLD = 0.4 # audeering valence below this number indicates distress. 0.5 is neutral, lower would be considered more negative

def is_distressed(checkin, avg_sentiment: float, drop: float) -> bool:
    text_low = checkin.sentiment_score is not None and checkin.sentiment_score < avg_sentiment - drop
    audio_low = checkin.audio_emotion_score is not None and checkin.audio_emotion_score < AUDIO_DISTRESS_THRESHOLD
    return text_low or audio_low # distress in either signal is enough to flag the checkin

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
        return None # there is less than 3 checkins meaning there is not enough history to compare against
    
    if is_on_cooldown(user_id, db):
        return None # a nudge has been sent already in the past 3 days

    recent = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user_id)
        .order_by(CheckIn.checkin_date.desc())
        .limit(3)
        .all()
    )

    if len(recent) >= 1 and recent[0].band_label == "High distress": # band labels don't require a scored baseline
        return create_nudge_flag(user_id, "band_high_distress_1d", db)

    if len(recent) >= 2:
        last_two = recent[:2]
        if all(c.band_label == "Significant difficulty" for c in last_two):
            return create_nudge_flag(user_id, "band_significant_2d", db)

    if baseline["sentiment_mean"] is None or baseline["sentiment_sd"] is None:
        return None # there are checkins but none have been scored yet to create a personal baseline
    
    avg_sentiment = baseline["sentiment_mean"]
    sd = baseline["sentiment_sd"]

    if len(recent) >= 2:
        last_two = recent[:2]
        if all(is_distressed(c, avg_sentiment, sd) for c in last_two):
            return create_nudge_flag(user_id, "sentiment_sustained_2d", db)
        
    if len(recent) >= 3:
        if all(is_distressed(c, avg_sentiment, sd) for c in recent):
            return create_nudge_flag(user_id, "sentiment_sustained_3d", db)
    
    if len(recent) >= 1:
        latest = recent[0]
        signal_low = is_distressed(latest, avg_sentiment, sd)
        sleep_low = latest.sleep_hours is not None and baseline["sleep_mean"] is not None and latest.sleep_hours < baseline["sleep_mean"]
        steps_low = latest.step_count is not None and baseline["steps_mean"] is not None and latest.step_count < baseline["steps_mean"]
        if signal_low and (sleep_low or steps_low):
            return create_nudge_flag(user_id, "sentiment_convergent", db)
        
    if len(recent) == 0 or (recent and (datetime.now(timezone.utc).date() - recent[0].checkin_date).days >= 3): # no checkins or the last one was more than 3 days ago
        return create_nudge_flag(user_id, "ghost_checkin_3d", db)
    
    return None