from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChatOut(BaseModel):
    id: int
    channel: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    last_message_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageIn(BaseModel):
    chat_id: Optional[int] = None
    content: str


class SendMessageOut(BaseModel):
    chat_id: int
    user_message: MessageOut
    assistant_message: MessageOut
    credits_remaining: int
