from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Admin(Base):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Service(Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)            # e.g. "Facebook 1"
    keyword: Mapped[str] = mapped_column(String(80), index=True)          # match in OTP text e.g. "FACEBOOK"
    emoji: Mapped[str] = mapped_column(String(16), default="📱")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Country(Base):
    __tablename__ = "countries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    code: Mapped[str] = mapped_column(String(8), index=True)              # e.g. "49"
    iso: Mapped[str] = mapped_column(String(4), default="")               # e.g. "DE"
    flag: Mapped[str] = mapped_column(String(16), default="🌍")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class TgUser(Base):
    __tablename__ = "tg_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(120), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    balance: Mapped[int] = mapped_column(Integer, default=0)              # cosmetic
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Number(Base):
    __tablename__ = "numbers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(32), index=True)            # full e164 without +
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"), index=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id", ondelete="CASCADE"), index=True)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("tg_users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_otp: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_otp_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    service: Mapped[Service] = relationship(lazy="joined")
    country: Mapped[Country] = relationship(lazy="joined")

    __table_args__ = (UniqueConstraint("phone", "service_id", name="uq_phone_service"),)


class Otp(Base):
    __tablename__ = "otps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(32))
    raw_text: Mapped[str] = mapped_column(Text, default="")
    service_hint: Mapped[str | None] = mapped_column(String(80), nullable=True)
    delivered_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("tg_users.id", ondelete="SET NULL"), nullable=True, index=True)
    matched_number_id: Mapped[int | None] = mapped_column(ForeignKey("numbers.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
