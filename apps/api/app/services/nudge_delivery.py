from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.checkin import CheckIn
from app.models.group import FriendAssignment, GroupMember
from app.models.notification import Notification
from app.models.nudge import NudgeFlag
from app.models.user import User

MESSAGES = {
    "sentiment_convergent": "It might be nice to check in on {name} today 💙",
    "sentiment_sustained_2d": "We think {name} could do with hearing from you. Would be worth reaching out when you can 💙",
    "sentiment_sustained_3d": "We're a bit concerned about {name}. We think they could really do with a friend right now 💙",
    "ghost_checkin_3d": "We haven't heard from {name} in a few days. Might be worth dropping them a message 💙",
    "band_significant_2d": "{name} has had a couple of really difficult days. They could probably do with hearing from someone they trust 💙",
    "band_high_distress_1d": "{name} is having a really hard time right now. It would mean a lot if you got in touch 💙"
}

def is_friend_active(user_id: int, db: Session) -> bool:
    cutoff = datetime.now(timezone.utc).date() - timedelta(days = 3) # if they've checked in within 3 days they're active enough to receive a nudge
    result = db.query(CheckIn).filter(
        CheckIn.user_id == user_id,
        CheckIn.checkin_date >= cutoff
    ).first()
    if result is not None:
        return True
    else:
        return False

def get_most_well_active_member(group_id: int, exclude_user_id: int, db: Session) -> int | None:
    cutoff = datetime.now(timezone.utc).date() - timedelta(days = 3) # they're active if they've checked in in the past 3 days
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id != exclude_user_id
    ).all()
    best_id = None
    best_score = None
    for member in members:
        checkin = db.query(CheckIn).filter(
            CheckIn.user_id == member.user_id,
            CheckIn.checkin_date >= cutoff,
            CheckIn.sentiment_score != None
        ).order_by(CheckIn.checkin_date.desc()).first()
        if checkin and (best_score is None or checkin.sentiment_score < best_score):
            best_score = checkin.sentiment_score
            best_id = member.user_id
    return best_id

def get_most_recent_member(group_id: int, exclude_user_id: int, db: Session) -> int | None:
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id != exclude_user_id
    ).all()
    latest_id = None
    latest_date = None
    for member in members:
        checkin = db.query(CheckIn).filter(
            CheckIn.user_id == member.user_id
        ).order_by(CheckIn.checkin_date.desc()).first() # no cutoff as this is a last resort, whoever checked in most recently
        if checkin and (latest_date is None or checkin.checkin_date > latest_date):
            latest_date = checkin.checkin_date
            latest_id = member.user_id
    return latest_id

def find_friend(user_id: int, db: Session) -> int | None:
    assignment = db.query(FriendAssignment).filter(
        FriendAssignment.user_id == user_id
    ).first()
    if assignment and is_friend_active(assignment.friend_id, db):
        return assignment.friend_id
    if not assignment:
        return None
    best = get_most_well_active_member(assignment.group_id, user_id, db)
    if best:
        return best
    return get_most_recent_member(assignment.group_id, user_id, db) 

def deliver(flag: NudgeFlag, db: Session) -> Notification | None:
    subject = db.query(User).filter(User.id == flag.user_id).first()
    if not subject:
        return None
    friend_id = find_friend(flag.user_id, db)
    if not friend_id:
        return None
    message = MESSAGES.get(flag.trigger_rule, "We think {name} could do with some support right now 💙")
    message = message.format(name = subject.first_name)
    notification = Notification(
        recipient_id = friend_id,
        nudge_flag_id = flag.id,
        message = message
    )
    db.add(notification)
    flag.sent_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)
    return notification
