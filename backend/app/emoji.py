"""Helpers for storing Telegram custom emoji IDs safely."""
from __future__ import annotations

import re


_ID_RE = re.compile(r"\d{12,32}")


def clean_custom_emoji_id(value: str | None) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    match = _ID_RE.search(raw)
    return match.group(0) if match else None