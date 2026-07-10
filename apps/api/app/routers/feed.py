from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.group import GroupMember
from app.models.feed import Post, Reaction
from app.schemas.feed import PostCreate, ReactionCreate, PostResponse, ReactionResponse

router = APIRouter(prefix = "/feed", tags = ["feed"])

@router.get("/groups/{group_id}", response_model = list[PostResponse])
def get_feed(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code = 403, detail = "You are not a member of this group.")
    posts = db.query(Post).filter(
        Post.group_id == group_id
    ).order_by(Post.created_at.asc()).all()
    result = []
    for post in posts:
        author = db.query(User).filter(
            User.id == post.author_id
        ).first() if post.author_id else None
        reactions = db.query(Reaction).filter(
            Reaction.post_id == post.id
        ).all()
        result.append(PostResponse(
            id = post.id,
            group_id = post.group_id,
            author_id = post.author_id,
            author_name = author.first_name if author else None,
            content = post.content,
            author_type = post.author_type,
            parent_post_id = post.parent_post_id,
            created_at = post.created_at,
            reactions = [ReactionResponse.model_validate(r) for r in reactions]
        ))
    return result
    
@router.post("/groups/{group_id}", response_model = PostResponse)
def create_post(group_id: int, payload: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code = 403, detail = "You are not a member of this group.")
    post = Post(
        group_id = group_id,
        author_id = current_user.id,
        content = payload.content,
        author_type = "member"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return PostResponse(
        id = post.id,
        group_id = post.group_id,
        author_id = post.author_id,
        author_name = current_user.first_name,
        content = post.content,
        author_type = post.author_type,
        parent_post_id = post.parent_post_id,
        created_at = post.created_at,
        reactions = []
    )

@router.post("/posts/{post_id}/react")
def add_reaction(post_id: int, payload: ReactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()
    if not post:
        raise HTTPException(status_code = 404, detail = "Post not found.")
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == post.group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code = 403, detail = "You are not a member of this group.")
    existing = db.query(Reaction).filter(
        Reaction.post_id == post_id,
        Reaction.user_id == current_user.id,
        Reaction.emoji == payload.emoji
    ).first()
    if existing:
        raise HTTPException(status_code = 400, detail = "You have already reacted with this emoji.")
    reaction = Reaction(post_id = post_id, user_id = current_user.id, emoji = payload.emoji)
    db.add(reaction)
    db.commit()
    return { "ok": True }

@router.delete("/posts/{post_id}/react")
def remove_reaction(post_id: int, emoji: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reaction = db.query(Reaction).filter(
        Reaction.post_id == post_id,
        Reaction.user_id == current_user.id,
        Reaction.emoji == emoji
    ).first()
    if not reaction:
        raise HTTPException(status_code = 404, detail = "Reaction not found.")
    db.delete(reaction)
    db.commit()
    return { "ok": True }

@router.post("/posts/{post_id}/reply", response_model = PostResponse)
def reply_to_post(post_id: int, payload: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    parent = db.query(Post).filter(
        Post.id == post_id
    ).first()
    if not parent:
        raise HTTPException(status_code = 404, detail = "Post not found.")
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == parent.group_id,
        GroupMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code = 403, detail = "You are not a member of this group.")
    post = Post(
        group_id = parent.group_id,
        author_id = current_user.id,
        content = payload.content,
        author_type = "member",
        parent_post_id = post_id
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return PostResponse(
        id = post.id,
        group_id = post.group_id,
        author_id = post.author_id,
        author_name = current_user.first_name,
        content = post.content,
        author_type = post.author_type,
        parent_post_id = post.parent_post_id,
        created_at = post.created_at,
        reactions = []
    )