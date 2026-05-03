from datetime import datetime

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth import current_admin
from ..config import settings
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
        "service_name": (num.service.name if num and num.service else None),
        "service_emoji": (num.service.emoji if num and num.service else None),
        "country_name": (num.country.name if num and num.country else None),
        "country_flag": (num.country.flag if num and num.country else None),
        "country_code": (num.country.code if num and num.country else None),
        "username": user.username if user else None,
        "first_name": user.first_name if user else None,
    }


async def _enrich(db: AsyncSession, rows: list[Otp]) -> list[dict]:
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


# ---------- Manual OTP injection (admin) ----------

class InjectIn(BaseModel):
    number_id: int
    code: str = Field(min_length=1, max_length=16)
    raw_text: str | None = None
    notify: bool = True


async def _send_telegram(chat_id: int, text: str, code: str) -> bool:
    if not settings.BOT_TOKEN:
        return False
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": {"inline_keyboard": [[
            {"text": f"📋 {code}", "copy_text": {"text": code}}
        ]]},
    }
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as sess:
            async with sess.post(url, json=payload) as r:
                d = await r.json(content_type=None)
                return bool(d.get("ok"))
    except Exception:
        return False


@router.post("/inject")
async def inject_otp(
    body: InjectIn,
    _: object = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-side OTP injection — saves an Otp row, marks the number, and (optionally) pushes to the
    assigned Telegram user. Useful for testing or recovering missed OTPs."""
    n = (await db.execute(
        select(Number).where(Number.id == body.number_id)
        .options(selectinload(Number.service), selectinload(Number.country))
    )).scalar_one_or_none()
    if not n:
        raise HTTPException(404, "Number not found")

    n.last_otp = body.code
    n.last_otp_at = datetime.utcnow()

    otp = Otp(
        phone=n.phone,
        code=body.code,
        raw_text=(body.raw_text or f"[manual injection by admin] code={body.code}")[:1000],
        service_hint=n.service.keyword if n.service else None,
        matched_number_id=n.id,
        delivered_to_user_id=n.assigned_user_id,
    )
    db.add(otp)
    await db.commit()
    await db.refresh(otp)

    delivered = False
    if body.notify and n.assigned_user_id:
        user = (await db.execute(select(TgUser).where(TgUser.id == n.assigned_user_id))).scalar_one_or_none()
        if user and not user.is_banned:
            flag = n.country.flag if n.country else "🌍"
            emo = n.service.emoji if n.service else "📱"
            iso = (n.country.iso or "").upper() if n.country else ""
            text = f"{flag} #{iso} {emo} <code>{n.phone}</code>\n\n🔑 <b>{body.code}</b>"
            delivered = await _send_telegram(user.tg_id, text, body.code)

    return {"ok": True, "otp_id": otp.id, "delivered": delivered}
