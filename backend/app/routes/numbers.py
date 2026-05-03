import re
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_admin
from ..db import get_db
from ..models import Number

router = APIRouter()


class NumberIn(BaseModel):
    phone: str
    service_id: int
    country_id: int
    provider_id: int | None = None
    enabled: bool = True


class BulkIn(BaseModel):
    service_id: int
    country_id: int
    provider_id: int | None = None
    phones: str  # newline / comma / space separated


def _assigned_filter(status: str | None) -> str | None:
    if status == "reserved":
        return "yes"
    if status == "available":
        return "no"
    return None


def _d(n: Number):
    return {
        "id": n.id,
        "phone": n.phone,
        "service_id": n.service_id,
        "country_id": n.country_id,
        "provider_id": n.provider_id,
        "service": n.service.name if n.service else None,
        "service_name": n.service.name if n.service else None,
        "service_code": n.service.code if n.service else None,
        "country": n.country.name if n.country else None,
        "country_name": n.country.name if n.country else None,
        "provider": n.provider.name if n.provider else None,
        "country_flag": n.country.flag if n.country else None,
        "country_code": n.country.code if n.country else None,
        "service_emoji": n.service.emoji if n.service else None,
        "assigned_user_id": n.assigned_user_id,
        "assigned_at": n.assigned_at.isoformat() if n.assigned_at else None,
        "last_otp": n.last_otp,
        "last_otp_at": n.last_otp_at.isoformat() if n.last_otp_at else None,
        "enabled": n.enabled,
    }


@router.get("")
async def list_numbers(
    service_id: int | None = None,
    country_id: int | None = None,
    assigned: str | None = None,
    status: str | None = None,
    q: str | None = None,
    _: object = Depends(current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Number)
    if service_id:
        stmt = stmt.where(Number.service_id == service_id)
    if country_id:
        stmt = stmt.where(Number.country_id == country_id)
    assigned = assigned or _assigned_filter(status)
    if assigned == "yes":
        stmt = stmt.where(Number.assigned_user_id.is_not(None))
    elif assigned == "no":
        stmt = stmt.where(Number.assigned_user_id.is_(None))
    if status == "disabled":
        stmt = stmt.where(Number.enabled == False)
    elif status == "used":
        stmt = stmt.where(Number.last_otp.is_not(None))
    elif status == "available":
        stmt = stmt.where(Number.enabled == True, Number.last_otp.is_(None), Number.assigned_user_id.is_(None))
    elif status == "reserved":
        stmt = stmt.where(Number.enabled == True, Number.last_otp.is_(None), Number.assigned_user_id.is_not(None))
    if q:
        stmt = stmt.where(Number.phone.ilike(f"%{q}%"))
    rows = (await db.execute(stmt.order_by(Number.id.desc()).limit(500))).scalars().all()
    return [_d(n) for n in rows]


@router.post("")
async def create_number(body: NumberIn, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    phone = re.sub(r"\D", "", body.phone)
    n = Number(phone=phone, service_id=body.service_id, country_id=body.country_id,
               provider_id=body.provider_id, enabled=body.enabled)
    db.add(n)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Number already exists for this service")
    await db.refresh(n)
    return _d(n)


@router.post("/bulk")
async def bulk(body: BulkIn, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    raw = re.split(r"[\s,;]+", body.phones.strip())
    phones = [re.sub(r"\D", "", p) for p in raw if p.strip()]
    inserted = 0
    for ph in phones:
        if not ph:
            continue
        exists = (await db.execute(select(Number).where(Number.phone == ph, Number.service_id == body.service_id))).scalar_one_or_none()
        if exists:
            continue
        db.add(Number(phone=ph, service_id=body.service_id, country_id=body.country_id,
                      provider_id=body.provider_id))
        inserted += 1
    await db.commit()
    return {"inserted": inserted, "submitted": len(phones)}


@router.put("/{nid}")
async def update_number(nid: int, body: NumberIn, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    n = (await db.execute(select(Number).where(Number.id == nid))).scalar_one_or_none()
    if not n:
        raise HTTPException(404)
    n.phone = re.sub(r"\D", "", body.phone)
    n.service_id = body.service_id
    n.country_id = body.country_id
    n.provider_id = body.provider_id
    n.enabled = body.enabled
    await db.commit()
    await db.refresh(n)
    return _d(n)


@router.delete("/{nid}", status_code=204)
async def delete_number(nid: int, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    n = (await db.execute(select(Number).where(Number.id == nid))).scalar_one_or_none()
    if n:
        await db.delete(n)
        await db.commit()
