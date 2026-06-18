from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.nudge import NudgeFlag
from app.models.checkin import CheckIn
from app.core.baseline import get_baseline

def evaluate_pending_nudges(db: Session):
    cutoff = datetime.now(timezone.utc) - timedelta(days = 3)
    pending = db.query(NudgeFlag).filter(
        NudgeFlag.sent_at != None,
        NudgeFlag.sent_at <= cutoff,
        NudgeFlag.evaluated_at == None
    ).all()

    for flag in pending:
        baseline = get_baseline(flag.user_id, db)
        if not baseline["sufficient_data"] or baseline["sentiment_mean"] is None:
            flag.outcome = "insufficient_data"
            flag.evaluated_at = datetime.now(timezone.utc)
            continue

        post_nudge = db.query(CheckIn).filter(
            CheckIn.user_id == flag.user_id,
            CheckIn.checkin_date > flag.sent_at.date()
        ).order_by(CheckIn.checkin_date.desc()).limit(3).all()

        if len(post_nudge) < 2:
            flag.outcome = "insufficient_data"
            flag.evaluated_at = datetime.now(timezone.utc)
            continue

        scored = [c for c in post_nudge if c.sentiment_score is not None]

        if len(scored) < 2:
            flag.outcome = "insufficient_data"
            flag.evaluated_at = datetime.now(timezone.utc)
            continue

        avg_post_nudge = sum(c.sentiment_score for c in scored) / len(scored)

        if avg_post_nudge >= baseline["sentiment_mean"]:
            flag.outcome = "improved" # not claiming that the nudge caused the improvement just recording the correlation
        else:
            flag.outcome = "no_change"
        
        flag.evaluated_at = datetime.now(timezone.utc)

    db.commit()