from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_admin
from ..db import get_db
from ..models import Otp

router = APIRouter()


@router.get("")
async def list_sms(_: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Otp).order_by(Otp.created_at.desc()).limit(200))).scalars().all()
    return [
        {
            "id": o.id,
            "phone": o.phone,
            "code": o.code,
            "service_hint": o.service_hint,
            "raw_text": o.raw_text,
            "delivered_to_user_id": o.delivered_to_user_id,
            "matched_number_id": o.matched_number_id,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in rows
    ]
