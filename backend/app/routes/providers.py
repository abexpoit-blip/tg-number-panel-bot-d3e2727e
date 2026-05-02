from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_admin
from ..db import get_db
from ..models import Provider

router = APIRouter()


class ProviderIn(BaseModel):
    name: str
    type: str = "iprn"
    base_url: str = "https://panel.iprn-sms.com"
    username: str
    password: str
    currency: str = "EUR"
    enabled: bool = True
    poll_interval: int = 15


class ProviderUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    base_url: str | None = None
    username: str | None = None
    password: str | None = None  # empty = keep existing
    currency: str | None = None
    enabled: bool | None = None
    poll_interval: int | None = None


def _d(p: Provider, *, secret: bool = True):
    return {
        "id": p.id,
        "name": p.name,
        "type": p.type,
        "base_url": p.base_url,
        "username": p.username,
        "password": "********" if secret else p.password,
        "currency": p.currency,
        "enabled": p.enabled,
        "poll_interval": p.poll_interval,
        "has_cookies": bool(p.cookies_json),
        "last_login_at": p.last_login_at.isoformat() if p.last_login_at else None,
        "last_poll_at": p.last_poll_at.isoformat() if p.last_poll_at else None,
        "last_error": p.last_error,
    }


@router.get("")
async def list_providers(_: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Provider).order_by(Provider.id))).scalars().all()
    return [_d(p) for p in rows]


@router.post("")
async def create_provider(body: ProviderIn, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    p = Provider(**body.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _d(p)


@router.put("/{pid}")
async def update_provider(pid: int, body: ProviderUpdate, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Provider).where(Provider.id == pid))).scalar_one_or_none()
    if not p:
        raise HTTPException(404)
    data = body.model_dump(exclude_unset=True)
    if data.get("password") in (None, "", "********"):
        data.pop("password", None)
    if "username" in data or "password" in data:
        # invalidate cookies on credential change
        p.cookies_json = ""
    for k, v in data.items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return _d(p)


@router.delete("/{pid}", status_code=204)
async def delete_provider(pid: int, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Provider).where(Provider.id == pid))).scalar_one_or_none()
    if p:
        await db.delete(p)
        await db.commit()


@router.post("/{pid}/clear-cookies")
async def clear_cookies(pid: int, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Provider).where(Provider.id == pid))).scalar_one_or_none()
    if not p:
        raise HTTPException(404)
    p.cookies_json = ""
    p.last_error = None
    await db.commit()
    return {"ok": True}
