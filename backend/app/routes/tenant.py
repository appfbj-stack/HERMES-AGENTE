from fastapi import APIRouter, Depends

from app.deps import get_current_modules, get_current_user
from app.models import TenantModule, User
from app.schemas import TenantModulesOut
from app.services.modules import build_modules_out

router = APIRouter(prefix="/tenant", tags=["tenant"])


@router.get("/modules", response_model=TenantModulesOut)
def get_tenant_modules(
    current_user: User = Depends(get_current_user),
    modules: TenantModule = Depends(get_current_modules),
):
    return build_modules_out(modules)
