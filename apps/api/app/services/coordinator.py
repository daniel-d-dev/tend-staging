from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.group import Group, GroupMember
from app.models.checkin import CheckIn
from app.models.nudge import NudgeFlag
from app.models.temperature import TemperatureCheck
from app.models.feed import Post
from app.core.database import SessionLocal
from app.core.message_generator import generate_message
from app.core.baseline import get_baseline
from app.core.low_energy_classifier import score_low_energy
from app.services.inference import is_distressed

def read_group_signals(group_id: int, db: Session) -> dict:
    cutoff = datetime.now(timezone.utc).date() - timedelta(days = 3) # they're active if they've checked in within the past three days
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).all()
    member_ids = [m.user_id for m in members]
    sentiment_scores = []
    distress_count = 0
    members_with_signal = 0
    for user_id in member_ids:
        checkin = db.query(CheckIn).filter(
            CheckIn.user_id == user_id,
            CheckIn.checkin_date >= cutoff
        ).order_by(CheckIn.checkin_date.desc()).first()
        if checkin and checkin.sentiment_score is not None:
            sentiment_scores.append(checkin.sentiment_score)
            baseline = get_baseline(db, user_id) # reuses the same distress check the main crisis pipeline uses (is_distressed against get_baseline), rather than a separate definition that could disagree with it for the same person on the same day. Members who don't have three or more check ins don't have a personal baseline yet, so they can't be checked this way. falling back to group-wide or fixed threshold for them would reintroduce the kind of absolute comparison this whole project deliberately leans away from, since people naturally write differently with it just being their personal style, not distress. Wouldn't say it's a fixable gap, just a real limit of needing someone's own history to judge what's normal for them
            if baseline["sufficient_data"] and baseline["sentiment_mean"] is not None and baseline["sentiment_sd"] is not None:
                members_with_signal += 1
                if is_distressed(checkin, baseline["sentiment_mean"], baseline["sentiment_sd"]):
                    distress_count += 1
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else None

    today = datetime.now(timezone.utc).date()
    week_start = today - timedelta(days = today.weekday()) # rewind to Monday of current week
    temperature_words = [tc.word for tc in db.query(TemperatureCheck).filter(
        TemperatureCheck.group_id == group_id,
        TemperatureCheck.week_start == week_start
    ).all()] # a separate feature, each member can submit one word describing their week, shown to the coordinator alongside the daily signals above
    low_energy_scores = [score_low_energy(word) for word in temperature_words]
    avg_low_energy = sum(low_energy_scores) / len(low_energy_scores) if low_energy_scores else None # used by select_activity_category to avoid suggesting something physical when the group's own words lean tired/drained, even on weeks where sentiment_score data doesn't yet tell the same story
    recent_flags = db.query(NudgeFlag).filter( # a flag that was created but never actually sent (blocked by the per-user cooldown) shouldn't count here, since these signals are about what the group has actually experienced recently. that's why this checks sent_at, not triggered_at
        NudgeFlag.user_id.in_(member_ids),
        NudgeFlag.sent_at.isnot(None),
        NudgeFlag.sent_at >= datetime.now(timezone.utc) - timedelta(days = 3)
    ).all()
    has_recent_flag = len(recent_flags) > 0
    has_high_distress = any(f.trigger_rule == "crisis_safety_net" for f in recent_flags) # shortens the cooldown below to 12 hours instead of 48
    return {
        "member_count": len(members),
        "active_count": len(sentiment_scores),
        "avg_sentiment": avg_sentiment,
        "distress_count": distress_count,
        "members_with_signal": members_with_signal,
        "temperature_words": temperature_words,
        "avg_low_energy": avg_low_energy,
        "has_recent_flag": has_recent_flag,
        "has_high_distress": has_high_distress
    }

def select_mode(signals: dict) -> str | None:
    if signals["has_high_distress"]:
        return "urgent"
    if signals["avg_sentiment"] is None:
        return None
    if signals["has_recent_flag"]:
        return "connective"
    avg_sentiment = signals["avg_sentiment"]
    distress_count = signals["distress_count"]
    members_with_signal = signals["members_with_signal"]
    majority_distressed = members_with_signal > 0 and distress_count >= members_with_signal / 2 # true if half or more of members with a personal baseline are currently distressed
    # thresholds below picked by feel, not tested rigorously like the crisis detection
    if avg_sentiment < 0.15 and distress_count == 0: # below 0.15 with nobody distressed suggests the group's genuinely doing fine, so lean into something fun
        return "activity"
    if avg_sentiment > 0.35 or majority_distressed: # above 0.35, or half the group struggling leans supportive regardless of the average, since a few members doing very well can mask several others who aren't
        return "supportive"
    return "connective"

LOW_ENERGY_THRESHOLD = 0.09 # calibrated against around 50 test words, deliberately kept out of the reference lists above so the test measured generalising to new words rather than just memorising the list. Every positive or neutral word scored below this, and 31 of 32 genuinely low-energy words scored above it. the one miss was "burnt" on its own, which is genuinely ambiguous (like food, sunburn, etc.), while the natural phrase "burnt out" is already in the reference list and gets caught fine

def select_activity_category(signals: dict) -> str: # Monday and Sunday start and end the week, so they get something reflective. Saturday's when people have more free time, so something physical makes sense. Weekdays stay social since people are busier and it's easier to achieve
    day = datetime.now(timezone.utc).weekday() # 0 is Monday and 6 is Sunday
    if day in (0, 6):
        category = "reflective"
    elif day == 5:
        category = "physical"
    else:
        category = "social"
    sentiment_low_mood = signals["avg_sentiment"] is not None and signals["avg_sentiment"] > 0.30
    temperature_low_energy = signals["avg_low_energy"] is not None and signals["avg_low_energy"] > LOW_ENERGY_THRESHOLD
    if category == "physical" and (sentiment_low_mood or temperature_low_energy):
        category = "social" # physical can help mild low mood but we avoid it when the group is genuinely struggling, whether that shows up in their check-in sentiment or in how they described their week
    return category

def run_coordinator(group_id: int, db: Session) -> None:
    last_post = db.query(Post).filter(
        Post.group_id == group_id,
        Post.author_type == "agent"
    ).order_by(Post.created_at.desc()).first()

    signals = read_group_signals(group_id, db)

    if signals["has_high_distress"]: # urgent cooldown only checks against the last urgent post, not the last post of any kind. a routine post a few hours ago shouldn't be able to hold back a genuinely urgent one, the same reasoning the per-user crisis override in nudge_delivery.py already follows
        last_urgent_post = db.query(Post).filter(
            Post.group_id == group_id,
            Post.author_type == "agent",
            Post.mode == "urgent"
        ).order_by(Post.created_at.desc()).first()
        if last_urgent_post:
            hours_since_urgent = (datetime.now(timezone.utc) - last_urgent_post.created_at).total_seconds() / 3600
            if hours_since_urgent < 12:
                return
    elif last_post:
        hours_since = (datetime.now(timezone.utc) - last_post.created_at).total_seconds() / 3600
        if hours_since < 48:
            return # standard cooldown of 48 hours

    mode = select_mode(signals)
    if mode is None:
        return

    category = select_activity_category(signals) if mode == "activity" else None
    last_post_summary = last_post.content if last_post else None
    message = generate_message(mode, category, signals, last_post_summary)

    post = Post(
        group_id = group_id,
        author_id = None,
        content = message,
        author_type = "agent",
        mode = mode
    )
    db.add(post)
    db.commit()

def coordinator_job():
    with SessionLocal() as db:
        groups = db.query(Group).all()
        for group in groups:
            try:
                run_coordinator(group.id, db)
            except Exception: # one group's failure (if Ollama is down or being slow for example) shouldn't stop every group after it in this run from being checked at all
                db.rollback() # clears any partial state left behind so the next group starts from a clean session