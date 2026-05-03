"""Telegram custom emoji helpers shared by bot message renderers."""
from __future__ import annotations

import html
import re
from typing import Any


_ID_RE = re.compile(r"\d{12,32}")


def clean_custom_emoji_id(value: str | None) -> str | None:
    """Return the numeric Telegram custom_emoji_id from raw admin input."""
    raw = (value or "").strip()
    if not raw:
        return None
    match = _ID_RE.search(raw)
    return match.group(0) if match else None


def tg_emoji_html(custom_emoji_id: str | None, fallback: str) -> str:
    """Render a premium emoji entity for Telegram HTML parse mode."""
    emoji_id = clean_custom_emoji_id(custom_emoji_id)
    safe_fallback = html.escape(fallback or "📱")
    if not emoji_id:
        return safe_fallback
    return f'<tg-emoji emoji-id="{emoji_id}">{safe_fallback}</tg-emoji>'


def service_emoji_html(service: Any | None) -> str:
    if not service:
        return "📱"
    return tg_emoji_html(getattr(service, "custom_emoji_id", None), getattr(service, "emoji", None) or "📱")


def flag_emoji_html(country: Any | None) -> str:
    if not country:
        return "🌍"
    return tg_emoji_html(getattr(country, "custom_emoji_id", None), getattr(country, "flag", None) or "🌍")