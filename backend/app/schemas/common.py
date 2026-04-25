from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LeadIn(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "new"
    notes: Optional[str] = None
    chat_id: Optional[int] = None


class LeadOut(LeadIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TaskIn(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    due_at: Optional[datetime] = None


class TaskOut(TaskIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CreditOut(BaseModel):
    balance: int

    class Config:
        from_attributes = True
