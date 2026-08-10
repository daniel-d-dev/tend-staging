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
    "ghost_checkin_3d": "We haven't heard from {name} in a few days. Might be worth dropping them a message 💙", # these are all deliberately soft and non alarming. Never quotes the checkin or uses words like "urgent" etc. Makes it more acceptable that this might fire a bit more often than it technically should. An unnecessary, gentle text better than the alternative
    "crisis_safety_net": "We think {name} could really do with hearing from someone they trust today 💙" # carries a little more weight than the gentler phrasing above, but deliberately isn't anything urgent sounding
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

def get_most_well_active_member(group_ids: list[int], exclude_user_id: int, db: Session) -> int | None: # picks whoever's doing best (lowest sentiment score) among active members. Checks every given group together in one pass, not one group at a time, so it can't end up picking a worse candidate just because their group was checked first. A fallback shouldn't land on someone who might be struggling themselves
    cutoff = datetime.now(timezone.utc).date() - timedelta(days = 3) # they're active if they've checked in in the past 3 days
    members = db.query(GroupMember).filter(
        GroupMember.group_id.in_(group_ids),
        GroupMember.user_id != exclude_user_id
    ).all()
    best_id = None
    best_score = None
    seen = set() # the same person can belong to more than one of these groups
    for member in members:
        if member.user_id in seen:
            continue
        seen.add(member.user_id)
        checkin = db.query(CheckIn).filter(
            CheckIn.user_id == member.user_id,
            CheckIn.checkin_date >= cutoff,
            CheckIn.sentiment_score != None
        ).order_by(CheckIn.checkin_date.desc()).first()
        if checkin and (best_score is None or checkin.sentiment_score < best_score):
            best_score = checkin.sentiment_score
            best_id = member.user_id
    return best_id

def get_most_recent_member(group_ids: list[int], exclude_user_id: int, db: Session) -> int | None:
    members = db.query(GroupMember).filter(
        GroupMember.group_id.in_(group_ids),
        GroupMember.user_id != exclude_user_id
    ).all()
    latest_id = None
    latest_date = None
    seen = set()
    for member in members:
        if member.user_id in seen:
            continue
        seen.add(member.user_id)
        checkin = db.query(CheckIn).filter(
            CheckIn.user_id == member.user_id
        ).order_by(CheckIn.checkin_date.desc()).first() # no cutoff as this is a last resort, whoever checked in most recently
        if checkin and (latest_date is None or checkin.checkin_date > latest_date):
            latest_date = checkin.checkin_date
            latest_id = member.user_id
    return latest_id

def find_friend(user_id: int, db: Session) -> int | None: # this is a three step fallback, starting with the person's own designated friend if they're active, then whichever other active group member seems to be doing best, then whoever's checked in most recently at all, as a last resort
    assignment = db.query(FriendAssignment).filter(
        FriendAssignment.user_id == user_id
    ).first()
    if assignment and is_friend_active(assignment.friend_id, db):
        return assignment.friend_id

    # if no designated friend, or the one they chose isn't active right now fall through to steps 2 and 3 instead of giving up. Search every group they're in, not just one, since there's no assignment telling us which group to prefer. Someone who never got round to assigning a friend shouldn't be left without any fallback at all, which is the reasoning for covering their case here too
    group_ids = [assignment.group_id] if assignment else [
        m.group_id for m in db.query(GroupMember).filter(GroupMember.user_id == user_id).all()
    ]
    if not group_ids:
        return None

    best = get_most_well_active_member(group_ids, user_id, db)
    if best:
        return best
    return get_most_recent_member(group_ids, user_id, db)

def needs_friend_assignment(user_id: int, db: Session) -> bool: # true only if they're in a group but haven't assigned a friend in any of them. Being in no group at all is a separate, earlier onboarding step this doesn't cover
    in_a_group = db.query(GroupMember).filter(GroupMember.user_id == user_id).first() is not None
    has_assignment = db.query(FriendAssignment).filter(FriendAssignment.user_id == user_id).first() is not None
    return in_a_group and not has_assignment

def is_on_cooldown(user_id: int, new_trigger_rule: str, db: Session) -> bool: # standard cooldown is 1 week since the last notification actually sent (not just flagged) but if the new flag is a fresh crisis_safety_net trigger, it can break through that standard cooldown early, as long as it's been at least 2 days since the last one was sent. A repeat of genuinely acute language is more urgent than an ongoing mild trend and shouldn't have to wait a full week to get through
    last_sent_flag = db.query(NudgeFlag).filter(
        NudgeFlag.user_id == user_id,
        NudgeFlag.sent_at.isnot(None)
    ).order_by(NudgeFlag.sent_at.desc()).first()
    if last_sent_flag is None:
        return False # never been notified before, nothing to be on cooldown from
    if new_trigger_rule == "crisis_safety_net":
        urgent_cutoff = datetime.now(timezone.utc) - timedelta(days = 2)
        if last_sent_flag.sent_at <= urgent_cutoff:
            return False # crisis, and it's been long enough, let this one through early
    # either this isn't a crisis trigger, or it is but the 2-day floor above hasn't been reached yet. Either way, fall back to the normal 1-week rule
    standard_cutoff = datetime.now(timezone.utc) - timedelta(days = 7)
    return last_sent_flag.sent_at > standard_cutoff

def queue_notification(flag: NudgeFlag, db: Session) -> Notification | None:
    if is_on_cooldown(flag.user_id, flag.trigger_rule, db):
        return None
    subject = db.query(User).filter(User.id == flag.user_id).first()
    if not subject:
        return None
    friend_id = find_friend(flag.user_id, db)
    if not friend_id:
        return None
    message = MESSAGES.get(flag.trigger_rule, "We think {name} could do with some support right now 💙") # fallback in case a trigger rule is ever added to inference.py without a matching message here
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
