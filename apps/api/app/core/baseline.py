from sqlalchemy.orm import Session
from app.models.checkin import CheckIn

def get_baseline(db: Session, user_id: int) -> dict:
    checkins = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user_id)
        .order_by(CheckIn.checkin_date.desc())
        .all()
    )

    if len(checkins) < 7: # may need changing in light of the pilot study
        return {"sufficient_data": False}
    
    sentiment_scores = [c.sentiment_score for c in checkins if c.sentiment_score is not None]
    sleep_values = [c.sleep_hours for c in checkins if c.sleep_hours is not None]
    step_values = [c.step_count for c in checkins if c.step_count is not None]

    return {
        "sufficient_data": True,
        "sentiment_mean": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else None, # None if user hasn't provided this data
        "sleep_mean": sum(sleep_values) / len(sleep_values) if sleep_values else None,
        "steps_mean": sum(step_values) / len(step_values) if step_values else None,
    }