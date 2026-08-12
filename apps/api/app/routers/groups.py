from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.group import Group, GroupMember, FriendAssignment
from app.models.feed import Post, Reaction
from app.models.temperature import TemperatureCheck
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse, GroupMemberInfo

router = APIRouter(prefix = "/groups", tags = ["groups"])

@router.post("/", response_model = GroupResponse)
def create_group(payload: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = Group(name = payload.name, created_by = current_user.id)
    db.add(group)
    db.flush() # assigns group.id before committing so we can attach the member to it
    member = GroupMember(group_id = group.id, user_id = current_user.id)
    db.add(member)
    db.commit()
    db.refresh(group)
    return group

@router.post("/join")
def join_group(join_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.join_code == join_code).first()
    if not group:
        raise HTTPException(status_code = 404, detail = "Group not found.")
    already_member = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.user_id == current_user.id
    ).first()
    if already_member:
        raise HTTPException(status_code = 400, detail = "You are already a member of this group.") # UniqueConstraint would catch this in any case but this gives the user a clearer error
    member = GroupMember(group_id = group.id, user_id = current_user.id)
    db.add(member)
    db.commit()
    return {"message": "Joined group successfully."}

@router.post("/{group_id}/friend")
def assign_friend(group_id: int, friend_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code = 403, detail = "You are not a member of this group.")
    if friend_id == current_user.id: # someone assigned as their own designated friend would mean nobody real ever gets notified if they're struggling
        raise HTTPException(status_code = 400, detail = "You can't assign yourself as your own designated friend.")
    friend_membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == friend_id
    ).first()
    if not friend_membership:
        raise HTTPException(status_code = 400, detail = "That user is not a member of this group.")
    assignment = db.query(FriendAssignment).filter(
        FriendAssignment.group_id == group_id,
        FriendAssignment.user_id == current_user.id
    ).first()
    if assignment:
        assignment.friend_id = friend_id # update existing assignment rather than creating a duplicate
    else:
        assignment = FriendAssignment(group_id = group_id, user_id = current_user.id, friend_id = friend_id)
        db.add(assignment)
    db.commit()
    return {"message": "Designated friend has been assigned successfully."}

@router.patch("/{group_id}", response_model = GroupResponse)
def rename_group(group_id: int, payload: GroupUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code = 404, detail = "Group not found.")
    if group.created_by != current_user.id: # only the creator can rename, same reasoning as delete below
        raise HTTPException(status_code = 403, detail = "Only the group's creator can rename it.")
    group.name = payload.name
    db.commit()
    db.refresh(group)
    return group

@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code = 404, detail = "Group not found.")
    if group.created_by != current_user.id: # deleting a group members are relying on shouldn't be a decision any single member can make alone
        raise HTTPException(status_code = 403, detail = "Only the group's creator can delete it.")

    post_ids = [p.id for p in db.query(Post.id).filter(Post.group_id == group_id).all()]
    if post_ids: # reactions reference posts, so they have to go first
        db.query(Reaction).filter(Reaction.post_id.in_(post_ids)).delete(synchronize_session = False)
    db.query(Post).filter(Post.group_id == group_id).delete(synchronize_session = False) # deletes replies alongside top-level posts in the same statement, avoiding any parent/child ordering issue
    db.query(TemperatureCheck).filter(TemperatureCheck.group_id == group_id).delete(synchronize_session = False)
    db.query(FriendAssignment).filter(FriendAssignment.group_id == group_id).delete(synchronize_session = False)
    db.query(GroupMember).filter(GroupMember.group_id == group_id).delete(synchronize_session = False)
    db.delete(group)
    db.commit()
    return {"message": "Group deleted successfully."}

@router.get("/me", response_model = list[GroupResponse])
def get_my_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memberships = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    group_ids = [m.group_id for m in memberships]
    return db.query(Group).filter(Group.id.in_(group_ids)).all()

@router.get("/{group_id}/members", response_model = list[GroupMemberInfo])
def get_group_members(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code = 403, detail = "You are not a member of this group.")
    members = db.query(GroupMember, User).join(User, User.id == GroupMember.user_id).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id != current_user.id
    ).all()
    return [{"user_id": u.id, "first_name": u.first_name} for _, u in members]