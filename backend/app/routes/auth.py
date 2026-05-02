from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import make_token, verify_pw
from ..db import get_db
from ..models import Admin

router = APIRouter()


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    email = str(body.email).strip().lower()
    row = (await db.execute(select(Admin).where(func.lower(Admin.email) == email))).scalar_one_or_none()
    if not row or not verify_pw(body.password, row.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return TokenOut(access_token=make_token(row.email))
