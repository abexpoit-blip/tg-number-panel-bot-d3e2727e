"""Parse OTP feed messages.

Examples seen in production:
  Nexus X Number Panel
  🇵🇭 PH • 📘 63997916XXXX • FACEBOOK
  (with inline button copy_text="45151088")

We extract:
  - phone digits (longest digit run >= 8)
  - service hint keyword (FACEBOOK, WHATSAPP, INSTAGRAM, TELEGRAM, TIKTOK, ...)
  - OTP code: prefer copy_text from inline keyboard; fallback to text regex.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


SERVICE_KEYWORDS = ["FACEBOOK", "WHATSAPP", "INSTAGRAM", "TELEGRAM", "TIKTOK", "GOOGLE", "TWITTER"]


@dataclass
class ParsedOtp:
    phone: str
    code: str
    service_hint: Optional[str]


def _extract_phone(text: str) -> Optional[str]:
    # Find runs of digits length >= 8, return the longest
    runs = re.findall(r"\d{8,}", text or "")
    if not runs:
        return None
    return max(runs, key=len)


def _extract_service(text: str) -> Optional[str]:
    up = (text or "").upper()
    for kw in SERVICE_KEYWORDS:
        if kw in up:
            return kw
    return None


def _extract_code_from_text(text: str) -> Optional[str]:
    # Look for explicit OTP patterns. Avoid grabbing the phone number.
    text = text or ""
    # Common: "code: 123456", "OTP: 123-456", "G-123456"
    m = re.search(r"(?:code|otp|pin|verification)[^\d]{0,8}([\d\-\s]{4,10})", text, re.IGNORECASE)
    if m:
        return re.sub(r"\D", "", m.group(1))
    # G-123456 style
    m = re.search(r"\b[A-Z]-(\d{4,8})\b", text)
    if m:
        return m.group(1)
    return None


def parse_message(text: str, copy_texts: list[str] | None = None) -> Optional[ParsedOtp]:
    phone = _extract_phone(text or "")
    if not phone:
        return None
    service = _extract_service(text or "")

    code: Optional[str] = None
    if copy_texts:
        # Prefer numeric copy_text values that are NOT the phone
        for ct in copy_texts:
            digits = re.sub(r"\D", "", ct or "")
            if 4 <= len(digits) <= 10 and digits != phone:
                code = digits
                break
    if not code:
        code = _extract_code_from_text(text or "")
    if not code:
        return None
    return ParsedOtp(phone=phone, code=code, service_hint=service)
