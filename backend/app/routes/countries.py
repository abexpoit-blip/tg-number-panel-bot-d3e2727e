from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_admin
from ..db import get_db
from ..models import Country

router = APIRouter()


class CountryIn(BaseModel):
    name: str
    code: str
    iso: str = ""
    flag: str = "🌍"
    custom_emoji_id: str | None = None
    enabled: bool = True


def _d(c: Country):
    return {
        "id": c.id, "name": c.name, "code": c.code, "iso": c.iso,
        "flag": c.flag, "custom_emoji_id": c.custom_emoji_id, "enabled": c.enabled,
    }


@router.get("")
async def list_countries(_: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Country).order_by(Country.name))).scalars().all()
    return [_d(c) for c in rows]


@router.post("")
async def create_country(body: CountryIn, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    c = Country(**body.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return _d(c)


@router.put("/{cid}")
async def update_country(cid: int, body: CountryIn, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    c = (await db.execute(select(Country).where(Country.id == cid))).scalar_one_or_none()
    if not c:
        raise HTTPException(404)
    for k, v in body.model_dump().items():
        setattr(c, k, v)
    await db.commit()
    return _d(c)


@router.delete("/{cid}", status_code=204)
async def delete_country(cid: int, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    c = (await db.execute(select(Country).where(Country.id == cid))).scalar_one_or_none()
    if c:
        await db.delete(c)
        await db.commit()
