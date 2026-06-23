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

def find_friend(user_id: int, db: Session) -> int | None:
    assignment = db.query(FriendAssignment).filter(
        FriendAssignment.user_id == user_id
    ).first()
    if assignment and is_friend_active(assignment.friend_id, db):
        return assignment.friend_id
    if not assignment:
        return None
    members = db.query(GroupMember).filter(
        GroupMember.group_id == assignment.group_id,
        GroupMember.user_id != user_id
    ).all() # if the designated friend isn't active then try anyone else in the group
    for member in members:
        if is_friend_active(member.user_id, db):
            return member.user_id
    return None

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
