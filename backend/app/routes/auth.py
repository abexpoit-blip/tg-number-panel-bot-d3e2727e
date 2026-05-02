from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import make_token, verify_pw
from ..db import get_db
from ..models import Admin

router = APIRouter()


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(Admin).where(Admin.email == body.email))).scalar_one_or_none()
    if not row or not verify_pw(body.password, row.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return TokenOut(access_token=make_token(row.email))
