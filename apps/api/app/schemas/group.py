from pydantic import BaseModel
from datetime import datetime

class GroupCreate(BaseModel):
    name: str

class GroupMemberResponse(BaseModel):
    user_id: int
    joined_at: datetime

    model_config = { "from_attributes": True }

class GroupResponse(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: datetime
    members: list[GroupMemberResponse] = []

    model_config = { "from_attributes": True }