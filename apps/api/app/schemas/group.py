from pydantic import BaseModel
from datetime import datetime

class GroupCreate(BaseModel):
    name: str

class GroupMemberResponse(BaseModel):
    user_id: int
    joined_at: datetime

    model_config = { "from_attributes": True }

class GroupMemberInfo(BaseModel):
    user_id: int
    first_name: str
    
class GroupResponse(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: datetime
    join_code: str
    members: list[GroupMemberResponse] = []

    model_config = { "from_attributes": True }