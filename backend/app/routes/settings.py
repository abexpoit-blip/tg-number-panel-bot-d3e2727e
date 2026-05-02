from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_admin
from ..db import get_db
from ..models import Setting

router = APIRouter()


class SetIn(BaseModel):
    value: str


@router.get("")
async def list_settings(_: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Setting))).scalars().all()
    return {r.key: r.value for r in rows}


@router.put("/{key}")
async def set_setting(key: str, body: SetIn, _: object = Depends(current_admin), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(Setting).where(Setting.key == key))).scalar_one_or_none()
    if row:
        row.value = body.value
    else:
        db.add(Setting(key=key, value=body.value))
    await db.commit()
    return {"key": key, "value": body.value}
