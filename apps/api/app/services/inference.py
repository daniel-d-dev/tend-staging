from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.checkin import CheckIn
from app.models.nudge import NudgeFlag
from app.core.baseline import get_baseline
from app.services.ensemble import evaluate_checkin

AUDIO_DISTRESS_THRESHOLD = 0.4 # audeering valence below this number indicates distress. 0.5 is neutral, lower would be considered more negative

def is_distressed(checkin, avg_sentiment: float, divergence: float) -> bool:
    text_distressed = checkin.sentiment_score is not None and checkin.sentiment_score > avg_sentiment + divergence
    audio_distressed = checkin.audio_emotion_score is not None and checkin.audio_emotion_score < AUDIO_DISTRESS_THRESHOLD
    return text_distressed or audio_distressed # distress in either signal is enough to flag the checkin

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
    if is_on_cooldown(user_id, db):
        return None # a nudge has been sent already in the past 3 days. applies to every rule below

    recent = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user_id)
        .order_by(CheckIn.checkin_date.desc())
        .limit(3)
        .all()
    )

    if len(recent) >= 1:
        latest = recent[0]
        safety_net_result = evaluate_checkin(latest.text_for_scoring)
        if safety_net_result["safety_net_triggered"]:
            return create_nudge_flag(user_id, "crisis_safety_net", db) # deliberately not gated behind checkin count or baseline sufficiency - this is the floor, it has to work for a first-time user on day one

    baseline = get_baseline(db, user_id)

    if not baseline["sufficient_data"]:
        return None # there is less than 3 checkins meaning there is not enough history to compare against - the trend rules below all need this, unlike the safety net check above

    if baseline["sentiment_mean"] is None or baseline["sentiment_sd"] is None:
        return None # there are checkins but none have been scored yet to create a personal baseline

    avg_sentiment = baseline["sentiment_mean"]
    sd = baseline["sentiment_sd"]

    if len(recent) >= 3: # three days at a milder dip count for as much as two days at a bigger one. lasting longer is itself part of what makes it worth flagging. without the lower bar here, this rule would almost never actually fire, since anything severe enough to trigger it at the same threshold as the 2 day rule would have already triggered that one first
        if all(is_distressed(c, avg_sentiment, sd * 0.75) for c in recent):
            return create_nudge_flag(user_id, "sentiment_sustained_3d", db)

    if len(recent) >= 2:
        last_two = recent[:2]
        if all(is_distressed(c, avg_sentiment, sd) for c in last_two):
            return create_nudge_flag(user_id, "sentiment_sustained_2d", db)

    if len(recent) >= 1:
        latest = recent[0]
        signal_low = is_distressed(latest, avg_sentiment, sd)
        sleep_low = latest.sleep_hours is not None and baseline["sleep_mean"] is not None and latest.sleep_hours < baseline["sleep_mean"]
        steps_low = latest.step_count is not None and baseline["steps_mean"] is not None and latest.step_count < baseline["steps_mean"]
        if signal_low and (sleep_low or steps_low): # the only rule here where two signals have to agree, unlike the OR only design everywhere else. sleep and steps alone don't mean much on their own as a late night or a rest day explains either one without anything being wrong, so this only fires when the person's actually describing feeling low too, and sleep/steps just back that up rather than triggering anything by themselves
            return create_nudge_flag(user_id, "sentiment_convergent", db)

    if len(recent) == 0 or (recent and (datetime.now(timezone.utc).date() - recent[0].checkin_date).days >= 3): # no checkins or the last one was more than 3 days ago
        return create_nudge_flag(user_id, "ghost_checkin_3d", db)

    return None