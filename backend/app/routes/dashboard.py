from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_admin
from ..db import get_db
from ..models import Number, Otp, TgUser

router = APIRouter()


@router.get("/dashboard")
async def dashboard(_: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    total_numbers = (await db.execute(select(func.count(Number.id)))).scalar_one()
    assigned_numbers = (await db.execute(select(func.count(Number.id)).where(Number.assigned_user_id.is_not(None)))).scalar_one()
    total_users = (await db.execute(select(func.count(TgUser.id)))).scalar_one()
    total_otps = (await db.execute(select(func.count(Otp.id)))).scalar_one()
    today = datetime.utcnow() - timedelta(hours=24)
    otps_24h = (await db.execute(select(func.count(Otp.id)).where(Otp.created_at >= today))).scalar_one()
    return {
        "total_numbers": total_numbers,
        "assigned_numbers": assigned_numbers,
        "available_numbers": total_numbers - assigned_numbers,
        "total_users": total_users,
        "total_otps": total_otps,
        "otps_24h": otps_24h,
    }
