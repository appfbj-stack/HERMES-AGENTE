from fastapi import APIRouter, Depends

from app.deps import get_current_credit
from app.schemas import CreditOut

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("", response_model=CreditOut)
def get_credits(credit=Depends(get_current_credit)):
    return credit

