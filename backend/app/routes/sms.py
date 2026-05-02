from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth import current_admin
from ..db import get_db
from ..models import Number, Otp, TgUser

router = APIRouter()


def _d(o: Otp, *, num: Number | None = None, user: TgUser | None = None):
    return {
        "id": o.id,
        "phone": o.phone,
        "code": o.code,
        "service_hint": o.service_hint,
        "raw_text": o.raw_text,
        "delivered_to_user_id": o.delivered_to_user_id,
        "matched_number_id": o.matched_number_id,
        "provider_id": o.provider_id,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        # Enriched fields for the live feed
        "service_name": (num.service.name if num and num.service else None),
        "service_emoji": (num.service.emoji if num and num.service else None),
        "country_name": (num.country.name if num and num.country else None),
        "country_flag": (num.country.flag if num and num.country else None),
        "country_code": (num.country.code if num and num.country else None),
        "username": user.username if user else None,
        "first_name": user.first_name if user else None,
    }


async def _enrich(db: AsyncSession, rows: list[Otp]) -> list[dict]:
    """Batch-load matched numbers + delivered users to avoid N+1."""
    num_ids = {o.matched_number_id for o in rows if o.matched_number_id}
    user_ids = {o.delivered_to_user_id for o in rows if o.delivered_to_user_id}
    nums: dict[int, Number] = {}
    users: dict[int, TgUser] = {}
    if num_ids:
        q = (await db.execute(
            select(Number).where(Number.id.in_(num_ids))
            .options(selectinload(Number.service), selectinload(Number.country))
        )).scalars().all()
        nums = {n.id: n for n in q}
    if user_ids:
        q = (await db.execute(select(TgUser).where(TgUser.id.in_(user_ids)))).scalars().all()
        users = {u.id: u for u in q}
    return [_d(o, num=nums.get(o.matched_number_id), user=users.get(o.delivered_to_user_id)) for o in rows]


@router.get("")
async def list_sms(
    limit: int = 200,
    _: object = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Otp).order_by(Otp.created_at.desc()).limit(min(max(1, limit), 500))
    )).scalars().all()
    return await _enrich(db, rows)


@router.get("/by-number/{number_id}")
async def list_sms_for_number(
    number_id: int,
    _: object = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
):
    n = (await db.execute(select(Number).where(Number.id == number_id))).scalar_one_or_none()
    if not n:
        raise HTTPException(404)
    rows = (await db.execute(
        select(Otp).where(Otp.phone == n.phone)
        .order_by(Otp.created_at.desc()).limit(100)
    )).scalars().all()
    return await _enrich(db, rows)
