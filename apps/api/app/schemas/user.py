from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    created_at: datetime

    model_config = { "from_attributes": True } # lets pydantic read directly from sqlalchemy objects

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer" # This is the standard token type for JWTs

class TokenData(BaseModel):
    user_id: Optional[int] = None # This is none if the token is missing or can't be decoded