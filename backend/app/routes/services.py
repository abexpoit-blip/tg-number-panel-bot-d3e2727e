from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_admin
from ..db import get_db
from ..models import Service

router = APIRouter()


class ServiceIn(BaseModel):
    name: str
    keyword: str
    emoji: str = "📱"
    enabled: bool = True
    sort_order: int = 0


def _to_dict(s: Service):
    return {"id": s.id, "name": s.name, "keyword": s.keyword, "emoji": s.emoji, "enabled": s.enabled, "sort_order": s.sort_order}


@router.get("")
async def list_services(_: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Service).order_by(Service.sort_order, Service.id))).scalars().all()
    return [_to_dict(s) for s in rows]


@router.post("")
async def create_service(body: ServiceIn, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    s = Service(**body.model_dump())
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return _to_dict(s)


@router.put("/{sid}")
async def update_service(sid: int, body: ServiceIn, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(Service).where(Service.id == sid))).scalar_one_or_none()
    if not s:
        raise HTTPException(404)
    for k, v in body.model_dump().items():
        setattr(s, k, v)
    await db.commit()
    return _to_dict(s)


@router.delete("/{sid}", status_code=204)
async def delete_service(sid: int, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(Service).where(Service.id == sid))).scalar_one_or_none()
    if s:
        await db.delete(s)
        await db.commit()
