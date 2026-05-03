"""Reset service emojis to canonical brand unicode so bot buttons show the
right icon (WhatsApp 🟢, Facebook 📘, Instagram 📷, Telegram ✈️, TikTok 🎵).

Telegram inline-button labels can only render plain unicode — premium
<tg-emoji> entities are NOT allowed in button text — so we standardise on
recognisable brand glyphs. Premium IDs (custom_emoji_id) are untouched and
still render in the message body.

Run:
    docker compose exec api python -m app.migrations.fix_service_emojis
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from ..db import SessionLocal
from ..models import Service


# Map matched by case-insensitive substring of name OR keyword
BRAND_EMOJI: list[tuple[tuple[str, ...], str]] = [
    (("whatsapp",), "🟢"),
    (("facebook", "fb"), "📘"),
    (("instagram", "ig"), "📷"),
    (("telegram", "tg"), "✈️"),
    (("tiktok", "tt"), "🎵"),
    (("signal",), "🔵"),
    (("viber",), "🟣"),
    (("imo",), "💬"),
    (("line",), "💚"),
]


def _pick(name: str, keyword: str) -> str | None:
    blob = f"{name} {keyword}".lower()
    for needles, emoji in BRAND_EMOJI:
        if any(n in blob for n in needles):
            return emoji
    return None


async def _run() -> None:
    fixed = 0
    async with SessionLocal() as s:
        rows = (await s.execute(select(Service))).scalars().all()
        for r in rows:
            want = _pick(r.name or "", r.keyword or "")
            if want and r.emoji != want:
                r.emoji = want
                fixed += 1
        await s.commit()
    print(f"service emojis fix: updated={fixed}")


if __name__ == "__main__":
    asyncio.run(_run())
