from pydantic import BaseModel
from datetime import datetime

class PostCreate(BaseModel):
    content: str

class ReactionCreate(BaseModel):
    emoji: str

class ReactionResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    user_id: int
    emoji: str

    model_config = { "from_attributes": True }

class PostResponse(BaseModel):
    id: int
    group_id: int
    author_id: int | None
    author_name: str | None
    content: str
    author_type: str
    parent_post_id: int | None
    created_at: datetime
    reactions: list[ReactionResponse]

    model_config = { "from_attributes": True }