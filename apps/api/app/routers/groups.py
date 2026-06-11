from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.group import Group, GroupMember
from app.schemas.group import GroupCreate, GroupResponse

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

@router.get("/me", response_model = list[GroupResponse])
def get_my_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memberships = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    group_ids = [m.group_id for m in memberships]
    return db.query(Group).filter(Group.id.in_(group_ids)).all()