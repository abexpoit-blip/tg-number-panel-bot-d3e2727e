"""Telegram bot — user-facing menu + OTP feed listener in one process."""
import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from sqlalchemy import select

from .config import settings
from .db import Country, Number, Otp, Service, SessionLocal, TgUser
from .parser import parse_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("bot")

bot: Bot | None = None
dp = Dispatcher()


# ============= UI =============

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤖 Get Number"), KeyboardButton(text="💰 Balance")],
            [KeyboardButton(text="📊 Status"), KeyboardButton(text="🌍 Available Country")],
        ],
        resize_keyboard=True,
    )


async def ensure_user(msg_user) -> TgUser:
    async with SessionLocal() as s:
        u = (await s.execute(select(TgUser).where(TgUser.tg_id == msg_user.id))).scalar_one_or_none()
        if not u:
            u = TgUser(tg_id=msg_user.id, username=msg_user.username, first_name=msg_user.first_name)
            s.add(u)
            await s.commit()
            await s.refresh(u)
        return u


# ============= Commands =============

@dp.message(CommandStart())
async def on_start(msg: Message):
    u = await ensure_user(msg.from_user)
    if u.is_banned:
        await msg.answer("⛔ You are banned.")
        return
    name = msg.from_user.first_name or "friend"
    await msg.answer(
        f"👋 <b>Welcome {name}!</b> ✊\n\n🟢 <b>Main Menu</b>\n📥 Please select an option below:",
        reply_markup=main_menu_kb(),
    )


@dp.message(F.text == "💰 Balance")
async def on_balance(msg: Message):
    u = await ensure_user(msg.from_user)
    await msg.answer(f"💰 Balance: <b>{u.balance}</b> credits\n\nThis service is currently <b>FREE</b>.")


@dp.message(F.text == "📊 Status")
async def on_status(msg: Message):
    u = await ensure_user(msg.from_user)
    async with SessionLocal() as s:
        rows = (await s.execute(select(Number).where(Number.assigned_user_id == u.id))).scalars().all()
    if not rows:
        await msg.answer("📭 You have no assigned numbers yet.\nTap 🤖 <b>Get Number</b> to begin.")
        return
    lines = ["📊 <b>Your active numbers:</b>\n"]
    for n in rows:
        otp_part = f"  ➜ OTP: <code>{n.last_otp}</code>" if n.last_otp else "  ⏳ Waiting…"
        lines.append(f"{n.country.flag if n.country else '🌍'} {n.service.emoji if n.service else '📱'} <code>+{n.phone}</code>\n{otp_part}\n")
    await msg.answer("\n".join(lines))


@dp.message(F.text == "🌍 Available Country")
async def on_countries(msg: Message):
    async with SessionLocal() as s:
        rows = (await s.execute(select(Country).where(Country.enabled == True).order_by(Country.name))).scalars().all()
    if not rows:
        await msg.answer("No countries configured yet.")
        return
    text = "🌍 <b>Available countries:</b>\n\n" + "\n".join(f"{c.flag} {c.name} (+{c.code})" for c in rows)
    await msg.answer(text)


# --------- Get Number flow ---------

@dp.message(F.text == "🤖 Get Number")
async def on_get_number(msg: Message):
    u = await ensure_user(msg.from_user)
    if u.is_banned:
        return
    async with SessionLocal() as s:
        services = (await s.execute(select(Service).where(Service.enabled == True).order_by(Service.sort_order, Service.id))).scalars().all()
    if not services:
        await msg.answer("No services available right now.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{sv.emoji} {sv.name}", callback_data=f"svc:{sv.id}")] for sv in services
    ])
    await msg.answer("🎚 <b>Select a Service:</b>", reply_markup=kb)


@dp.callback_query(F.data.startswith("svc:"))
async def on_service_chosen(cb: CallbackQuery):
    svc_id = int(cb.data.split(":")[1])
    async with SessionLocal() as s:
        # countries that have at least one available number for this service
        rows = (await s.execute(
            select(Country, Number)
            .join(Number, Number.country_id == Country.id)
            .where(Number.service_id == svc_id, Number.enabled == True, Number.assigned_user_id.is_(None))
        )).all()
    if not rows:
        await cb.message.edit_text("😕 No numbers available for this service. Try again later.")
        await cb.answer()
        return
    counts: dict[int, tuple[Country, int]] = {}
    for c, _n in rows:
        if c.id not in counts:
            counts[c.id] = (c, 0)
        counts[c.id] = (c, counts[c.id][1] + 1)
    buttons = []
    for cid, (c, cnt) in sorted(counts.items(), key=lambda kv: -kv[1][1]):
        buttons.append([InlineKeyboardButton(
            text=f"{c.flag} {c.name} (+{c.code}) - {cnt}",
            callback_data=f"ctry:{svc_id}:{cid}",
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Back To Services", callback_data="back:svc")])
    async with SessionLocal() as s:
        sv = (await s.execute(select(Service).where(Service.id == svc_id))).scalar_one()
    await cb.message.edit_text(
        f"{sv.emoji} <b>Select country for {sv.name}:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await cb.answer()


@dp.callback_query(F.data == "back:svc")
async def back_to_services(cb: CallbackQuery):
    async with SessionLocal() as s:
        services = (await s.execute(select(Service).where(Service.enabled == True).order_by(Service.sort_order, Service.id))).scalars().all()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{sv.emoji} {sv.name}", callback_data=f"svc:{sv.id}")] for sv in services
    ])
    await cb.message.edit_text("🎚 <b>Select a Service:</b>", reply_markup=kb)
    await cb.answer()


@dp.callback_query(F.data.startswith("ctry:"))
async def on_country_chosen(cb: CallbackQuery):
    _, svc_id_s, ctry_id_s = cb.data.split(":")
    svc_id, ctry_id = int(svc_id_s), int(ctry_id_s)
    u = await ensure_user(cb.from_user)
    async with SessionLocal() as s:
        # assign up to 5 available numbers to this user
        avail = (await s.execute(
            select(Number).where(
                Number.service_id == svc_id,
                Number.country_id == ctry_id,
                Number.enabled == True,
                Number.assigned_user_id.is_(None),
            ).limit(5)
        )).scalars().all()
        if not avail:
            await cb.message.edit_text("😕 No more numbers in this country. Tap 🌍 Change Country.")
            await cb.answer()
            return
        for n in avail:
            n.assigned_user_id = u.id
            n.assigned_at = datetime.utcnow()
        await s.commit()
        sv = (await s.execute(select(Service).where(Service.id == svc_id))).scalar_one()
        ctry = (await s.execute(select(Country).where(Country.id == ctry_id))).scalar_one()
    await render_user_numbers(cb.message, u.id, svc_id, ctry_id, sv, ctry, edit=True)
    await cb.answer()


async def render_user_numbers(target: Message, user_pk: int, svc_id: int, ctry_id: int, sv: Service, ctry: Country, edit: bool):
    async with SessionLocal() as s:
        nums = (await s.execute(
            select(Number).where(
                Number.assigned_user_id == user_pk,
                Number.service_id == svc_id,
                Number.country_id == ctry_id,
            ).limit(5)
        )).scalars().all()

    header = f"{ctry.flag} {sv.emoji} <b>{ctry.name} Number:</b>\n⏳ Waiting for OTP…\n"
    rows: list[list[InlineKeyboardButton]] = []
    for n in nums:
        if n.last_otp:
            label = f"{sv.emoji} +{n.phone}  ➜  {n.last_otp}"
            copy = f"+{n.phone}|{n.last_otp}"
        else:
            label = f"{sv.emoji} 📋 +{n.phone}"
            copy = f"+{n.phone}"
        rows.append([InlineKeyboardButton(text=label, copy_text={"text": copy})])
    rows.append([InlineKeyboardButton(text="🔄 Change Number", callback_data=f"chg:{svc_id}:{ctry_id}")])
    rows.append([InlineKeyboardButton(text="🌍 Change Country", callback_data=f"svc:{svc_id}")])
    rows.append([InlineKeyboardButton(text="🔑 Get OTP", callback_data=f"refresh:{svc_id}:{ctry_id}")])

    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    if edit:
        try:
            await target.edit_text(header, reply_markup=kb)
        except Exception:
            await target.answer(header, reply_markup=kb)
    else:
        await target.answer(header, reply_markup=kb)


@dp.callback_query(F.data.startswith("refresh:"))
async def on_refresh(cb: CallbackQuery):
    _, svc_id_s, ctry_id_s = cb.data.split(":")
    svc_id, ctry_id = int(svc_id_s), int(ctry_id_s)
    u = await ensure_user(cb.from_user)
    async with SessionLocal() as s:
        sv = (await s.execute(select(Service).where(Service.id == svc_id))).scalar_one()
        ctry = (await s.execute(select(Country).where(Country.id == ctry_id))).scalar_one()
    await render_user_numbers(cb.message, u.id, svc_id, ctry_id, sv, ctry, edit=True)
    await cb.answer("Refreshed")


@dp.callback_query(F.data.startswith("chg:"))
async def on_change_number(cb: CallbackQuery):
    _, svc_id_s, ctry_id_s = cb.data.split(":")
    svc_id, ctry_id = int(svc_id_s), int(ctry_id_s)
    u = await ensure_user(cb.from_user)
    async with SessionLocal() as s:
        # release current numbers without OTP and assign new ones
        current = (await s.execute(
            select(Number).where(
                Number.assigned_user_id == u.id,
                Number.service_id == svc_id,
                Number.country_id == ctry_id,
                Number.last_otp.is_(None),
            )
        )).scalars().all()
        for n in current:
            n.assigned_user_id = None
            n.assigned_at = None
        await s.flush()
        avail = (await s.execute(
            select(Number).where(
                Number.service_id == svc_id,
                Number.country_id == ctry_id,
                Number.enabled == True,
                Number.assigned_user_id.is_(None),
            ).limit(5)
        )).scalars().all()
        for n in avail:
            n.assigned_user_id = u.id
            n.assigned_at = datetime.utcnow()
        await s.commit()
        sv = (await s.execute(select(Service).where(Service.id == svc_id))).scalar_one()
        ctry = (await s.execute(select(Country).where(Country.id == ctry_id))).scalar_one()
    await render_user_numbers(cb.message, u.id, svc_id, ctry_id, sv, ctry, edit=True)
    await cb.answer("New numbers assigned")


# ============= OTP feed listener =============

def _extract_copy_texts(message: Message) -> list[str]:
    out: list[str] = []
    if message.reply_markup and message.reply_markup.inline_keyboard:
        for row in message.reply_markup.inline_keyboard:
            for btn in row:
                # aiogram 3 uses .copy_text attribute (CopyTextButton)
                ct = getattr(btn, "copy_text", None)
                if ct is not None:
                    txt = getattr(ct, "text", None) or (ct.get("text") if isinstance(ct, dict) else None)
                    if txt:
                        out.append(txt)
    return out


@dp.channel_post()
@dp.edited_channel_post()
async def on_feed_post(msg: Message):
    if not settings.OTP_FEED_CHANNEL_ID or msg.chat.id != settings.OTP_FEED_CHANNEL_ID:
        return
    text = (msg.text or msg.caption or "")
    copy_texts = _extract_copy_texts(msg)
    parsed = parse_message(text, copy_texts)
    if not parsed:
        log.info("Feed message ignored (no parse): %s", text[:80])
        return

    log.info("Parsed OTP phone=%s code=%s service=%s", parsed.phone, parsed.code, parsed.service_hint)

    async with SessionLocal() as s:
        # find a number matching the phone (and optionally service)
        stmt = select(Number).where(Number.phone == parsed.phone, Number.assigned_user_id.is_not(None))
        match = (await s.execute(stmt)).scalars().first()
        otp_row = Otp(
            phone=parsed.phone,
            code=parsed.code,
            raw_text=text[:1000],
            service_hint=parsed.service_hint,
        )
        if match:
            match.last_otp = parsed.code
            match.last_otp_at = datetime.utcnow()
            otp_row.matched_number_id = match.id
            otp_row.delivered_to_user_id = match.assigned_user_id
            user = (await s.execute(select(TgUser).where(TgUser.id == match.assigned_user_id))).scalar_one_or_none()
        else:
            user = None
        s.add(otp_row)
        await s.commit()

        # forward to user
        if match and user and not user.is_banned:
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=f"📋 +{match.phone} | {parsed.code}",
                    copy_text={"text": f"+{match.phone}|{parsed.code}"},
                )
            ]])
            try:
                await bot.send_message(
                    user.tg_id,
                    f"🔔 <b>New OTP received!</b>\n\n"
                    f"📱 Number: <code>+{match.phone}</code>\n"
                    f"🔑 OTP: <code>{parsed.code}</code>\n\n"
                    f"Tap below to copy <b>number|otp</b>:",
                    reply_markup=kb,
                )
            except Exception as e:
                log.exception("Failed to send OTP to user %s: %s", user.tg_id, e)


# ============= Entrypoint =============

async def main():
    global bot
    if not settings.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is required — set it in your .env file")
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    log.info("Starting bot. Brand=%s Feed=%s", settings.BOT_BRAND_NAME, settings.OTP_FEED_CHANNEL_ID)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
