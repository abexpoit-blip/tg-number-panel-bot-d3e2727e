from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .auth import hash_pw
from .config import settings
from .db import Base, SessionLocal, engine
from .models import Admin, Country, Service
from .routes import auth as auth_routes
from .routes import countries, dashboard, numbers, services, settings as settings_routes, sms, users, withdrawals


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as s:
        # seed admin
        existing = (await s.execute(select(Admin).where(Admin.email == settings.ADMIN_EMAIL))).scalar_one_or_none()
        if not existing:
            s.add(Admin(email=settings.ADMIN_EMAIL, password_hash=hash_pw(settings.ADMIN_PASSWORD)))
        # seed default services
        if not (await s.execute(select(Service))).first():
            defaults = [
                ("WhatsApp", "WHATSAPP", "🟢", 1),
                ("Facebook 1", "FACEBOOK", "📘", 2),
                ("Facebook 2", "FACEBOOK", "📘", 3),
                ("Instagram", "INSTAGRAM", "📷", 4),
                ("Telegram", "TELEGRAM", "✈️", 5),
                ("WhatsApp 2", "WHATSAPP", "🟢", 6),
                ("TikTok", "TIKTOK", "🎵", 7),
            ]
            for name, kw, emoji, order in defaults:
                s.add(Service(name=name, keyword=kw, emoji=emoji, sort_order=order))
        # seed common countries
        if not (await s.execute(select(Country))).first():
            ctry = [
                ("Germany", "49", "DE", "🇩🇪"),
                ("Senegal", "221", "SN", "🇸🇳"),
                ("Tanzania", "255", "TZ", "🇹🇿"),
                ("Burundi", "257", "BI", "🇧🇮"),
                ("Timor", "670", "TL", "🇹🇱"),
                ("Uzbekistan", "998", "UZ", "🇺🇿"),
                ("Philippines", "63", "PH", "🇵🇭"),
                ("Myanmar", "95", "MM", "🇲🇲"),
                ("Venezuela", "58", "VE", "🇻🇪"),
            ]
            for name, code, iso, flag in ctry:
                s.add(Country(name=name, code=code, iso=iso, flag=flag))
        await s.commit()
    yield


app = FastAPI(title="Seven1tel Panel API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(services.router, prefix="/services", tags=["services"])
app.include_router(countries.router, prefix="/countries", tags=["countries"])
app.include_router(numbers.router, prefix="/numbers", tags=["numbers"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(withdrawals.router, prefix="/withdrawals", tags=["withdrawals"])
app.include_router(sms.router, prefix="/sms", tags=["sms"])
app.include_router(settings_routes.router, prefix="/settings", tags=["settings"])


@app.get("/health")
async def health():
    return {"ok": True}
