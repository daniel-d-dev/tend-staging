from pydantic import BaseModel
from datetime import datetime

class NotificationResponse(BaseModel):
    id: int
    recipient_id: int
    nudge_flag_id: int
    message: str
    is_read: bool
    created_at: datetime

    model_config = { "from_attributes": True }