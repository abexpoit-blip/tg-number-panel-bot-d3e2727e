"""Background worker: poll all enabled providers, deliver matched OTPs to bot users.

Runs in the same process as the aiogram bot via asyncio.create_task.
Uses a per-(phone, code) dedup cache to avoid resending the same OTP.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from .db import Number, Otp, Provider, SessionLocal, Service, TgUser
from .scrapers.iprn import IprnClient, iterate_provider

if TYPE_CHECKING:
    from aiogram import Bot

log = logging.getLogger("worker.providers")


def _service_label(svc: Service | None) -> str:
    if not svc:
        return "📱"
    return f"{svc.emoji} {svc.name}"


def _service_emoji_html(svc: Service | None) -> str:
    """Use Telegram premium custom emoji if configured, else unicode fallback."""
    if not svc:
        return "📱"
    if svc.custom_emoji_id:
        return f'<tg-emoji emoji-id="{svc.custom_emoji_id}">{svc.emoji}</tg-emoji>'
    return svc.emoji


def _flag_emoji_html(c) -> str:
    if not c:
        return "🌍"
    if getattr(c, "custom_emoji_id", None):
        return f'<tg-emoji emoji-id="{c.custom_emoji_id}">{c.flag}</tg-emoji>'
    return c.flag or "🌍"


class _Dedup:
    def __init__(self, cap: int = 5000) -> None:
        self._seen: set[tuple[str, str]] = set()
        self._order: list[tuple[str, str]] = []
        self._cap = cap

    def add(self, k: tuple[str, str]) -> bool:
        if k in self._seen:
            return False
        self._seen.add(k)
        self._order.append(k)
        if len(self._order) > self._cap:
            old = self._order.pop(0)
            self._seen.discard(old)
        return True


_DEDUP = _Dedup()


async def _deliver(bot: "Bot", row, provider: Provider) -> None:
    code = row.extract_code()
    if not code:
        return
    if not _DEDUP.add((row.phone, code)):
        return

    async with SessionLocal() as s:
        # Find an assigned number that matches this phone
        match = (await s.execute(
            select(Number).where(Number.phone == row.phone, Number.assigned_user_id.is_not(None))
        )).scalars().first()

        otp = Otp(
            phone=row.phone, code=code,
            raw_text=(row.message or "")[:1000],
            service_hint=row.cli or row.name,
            provider_id=provider.id,
        )
        user: TgUser | None = None
        svc: Service | None = None
        if match:
            match.last_otp = code
            match.last_otp_at = datetime.utcnow()
            otp.matched_number_id = match.id
            otp.delivered_to_user_id = match.assigned_user_id
            user = (await s.execute(select(TgUser).where(TgUser.id == match.assigned_user_id))).scalar_one_or_none()
            svc = (await s.execute(select(Service).where(Service.id == match.service_id))).scalar_one_or_none()
        s.add(otp)
        await s.commit()

    if not (match and user and not user.is_banned):
        return

    emoji = _service_emoji_html(svc)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"📋 +{row.phone} | {code}",
                             copy_text={"text": f"+{row.phone}|{code}"})
    ]])
    try:
        await bot.send_message(
            user.tg_id,
            f"🔔 <b>New OTP received!</b>\n\n"
            f"{emoji} <b>{(svc.name if svc else 'Service')}</b>\n"
            f"📱 Number: <code>+{row.phone}</code>\n"
            f"🔑 OTP: <code>{code}</code>\n\n"
            f"Tap below to copy <b>number|otp</b>:",
            reply_markup=kb,
        )
    except Exception as e:
        log.exception("Failed to deliver OTP to %s: %s", user.tg_id, e)


async def _save_cookies(provider_id: int, cookies_json: str) -> None:
    async with SessionLocal() as s:
        p = (await s.execute(select(Provider).where(Provider.id == provider_id))).scalar_one_or_none()
        if p:
            p.cookies_json = cookies_json
            p.last_login_at = datetime.utcnow()
            p.last_error = None
            await s.commit()


async def _record_status(provider_id: int, error: str | None = None) -> None:
    async with SessionLocal() as s:
        p = (await s.execute(select(Provider).where(Provider.id == provider_id))).scalar_one_or_none()
        if p:
            p.last_poll_at = datetime.utcnow()
            p.last_error = error
            await s.commit()


async def _run_provider(bot: "Bot", provider: Provider) -> None:
    """Polling loop for one provider with exponential backoff + circuit breaker.

    Failure handling (protects the upstream panel & our IP):
      * each consecutive error doubles the sleep, capped at 5 minutes
      * after 8 consecutive errors -> stop polling, mark provider with last_error
        and require admin to "Clear cookies" / toggle enabled to retry.
    """
    log.info("starting provider loop name=%s currency=%s interval=%ss",
             provider.name, provider.currency, provider.poll_interval)
    client = IprnClient(provider.base_url, provider.username, provider.password,
                        provider.currency, provider.cookies_json or "")

    base_interval = max(10, provider.poll_interval or 15)
    backoff = base_interval
    consecutive_errors = 0
    MAX_BACKOFF = 300        # 5 minutes
    MAX_CONSECUTIVE = 8      # then stop until operator intervention

    if not provider.cookies_json:
        try:
            await client.login()
            await _save_cookies(provider.id, client.cookies_json())
        except Exception as e:
            log.error("provider %s initial login failed: %s", provider.name, e)
            await _record_status(provider.id, f"login: {e}")
            consecutive_errors = 1
            backoff = min(MAX_BACKOFF, backoff * 2)

    while True:
        try:
            async for row in iterate_provider(client):
                await _deliver(bot, row, provider)
            await _save_cookies(provider.id, client.cookies_json())
            await _record_status(provider.id, None)
            consecutive_errors = 0
            backoff = base_interval
        except Exception as e:
            consecutive_errors += 1
            msg = f"{type(e).__name__}: {e}"
            log.warning("provider %s poll error #%d: %s",
                        provider.name, consecutive_errors, msg)
            await _record_status(provider.id, msg[:500])
            if consecutive_errors >= MAX_CONSECUTIVE:
                log.error("provider %s disabled after %d failures — operator must intervene",
                          provider.name, consecutive_errors)
                await _record_status(
                    provider.id,
                    f"STOPPED after {consecutive_errors} failures: {msg[:400]}",
                )
                return  # exit the loop; providers_main will restart only if row changes
            backoff = min(MAX_BACKOFF, max(base_interval, backoff * 2))
        await asyncio.sleep(backoff)


async def providers_main(bot: "Bot") -> None:
    """Top-level loop: discover enabled providers and start a task per provider."""
    tasks: dict[int, asyncio.Task] = {}
    while True:
        try:
            async with SessionLocal() as s:
                rows = (await s.execute(select(Provider).where(Provider.enabled == True))).scalars().all()
            current_ids = {p.id for p in rows}
            # cancel removed/disabled
            for pid in list(tasks):
                if pid not in current_ids or tasks[pid].done():
                    tasks[pid].cancel()
                    tasks.pop(pid, None)
            # start new
            for p in rows:
                if p.id not in tasks:
                    tasks[p.id] = asyncio.create_task(_run_provider(bot, p))
        except Exception as e:
            log.exception("providers_main loop error: %s", e)
        await asyncio.sleep(20)
