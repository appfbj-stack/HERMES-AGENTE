from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_tenant, get_current_user
from app.models import Chat, User
from app.schemas import AssignChatRequest, ChatOut, ToggleAIRequest

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatOut])
def list_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Chat)
        .filter(Chat.tenant_id == current_user.tenant_id)
        .order_by(Chat.last_message_at.desc().nullslast(), Chat.created_at.desc())
        .all()
    )


@router.get("/{chat_id}", response_model=ChatOut)
def get_chat(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.tenant_id == current_user.tenant_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.post("/{chat_id}/assign", response_model=ChatOut)
def assign_chat(
    chat_id: int,
    payload: AssignChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant=Depends(get_current_tenant),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.tenant_id == current_user.tenant_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    assignee = db.query(User).filter(User.id == payload.assigned_user_id, User.tenant_id == tenant.id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="User not found")

    chat.assigned_user_id = assignee.id
    chat.status = "human"
    db.commit()
    db.refresh(chat)
    return chat


@router.post("/{chat_id}/toggle-ai", response_model=ChatOut)
def toggle_ai(
    chat_id: int,
    payload: ToggleAIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.tenant_id == current_user.tenant_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat.ai_paused = payload.ai_paused
    db.commit()
    db.refresh(chat)
    return chat

