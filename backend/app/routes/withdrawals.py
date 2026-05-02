from fastapi import APIRouter, Depends

from ..auth import current_admin

router = APIRouter()


# Refer & Earn / Withdrawals are disabled in this build (free service).
# Endpoints kept so the admin panel UI doesn't 404.
@router.get("")
async def list_withdrawals(status: str | None = None, _: object = Depends(current_admin)):
    return []
