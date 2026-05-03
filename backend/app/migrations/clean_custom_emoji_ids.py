"""One-shot repair: normalize custom_emoji_id in services & countries.

Run inside the api container:
    docker compose exec api python -m app.migrations.clean_custom_emoji_ids
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from ..db import SessionLocal
from ..emoji import clean_custom_emoji_id
from ..models import Country, Service


async def _run() -> None:
    fixed = 0
    cleared = 0
    async with SessionLocal() as s:
        for Model in (Service, Country):
            rows = (await s.execute(select(Model))).scalars().all()
            for r in rows:
                raw = r.custom_emoji_id
                if raw is None or raw == "":
                    continue
                cleaned = clean_custom_emoji_id(raw)
                if cleaned != raw:
                    r.custom_emoji_id = cleaned
                    if cleaned is None:
                        cleared += 1
                    else:
                        fixed += 1
        await s.commit()
    print(f"custom_emoji_id repair: normalized={fixed} cleared_invalid={cleared}")


if __name__ == "__main__":
    asyncio.run(_run())
