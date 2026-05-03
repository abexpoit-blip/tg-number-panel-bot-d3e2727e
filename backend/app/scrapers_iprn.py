"""IPRN-SMS panel scraper.

Login flow:
  GET  /login         -> obtain PHPSESSID cookie + CSRF token from form
  POST /login_check   -> _csrf_token + _username + _password + _remember_me + _submit
  GET  /premium_number/stats/sms?currency=XXX&range_filter=...

The CSRF token is mandatory — without it Symfony silently rejects the login
and bounces back to /login, which previously caused the scraper to retry
in a tight loop (the IP-block risk our manager warned about).

This scraper is RESPECTFUL:
  * one in-flight login at a time (asyncio.Lock)
  * exponential backoff on errors (5s -> 5min cap)
  * stops polling after too many consecutive failures (operator must intervene)
  * cookies persisted to DB so we re-use the session across restarts
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import AsyncIterator

import aiohttp
from bs4 import BeautifulSoup

log = logging.getLogger("scraper.iprn")

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


@dataclass
class IprnRow:
    source: str
    name: str
    phone: str          # digits only
    cli: str            # sender / from
    payout: str
    message: str
    notified: str
    created: str

    def extract_code(self) -> str | None:
        # Common OTP patterns in IPRN messages: "123 456", "123-456", "G-123456"
        m = re.search(r"\b(\d{3}[- ]?\d{3,4})\b", self.message)
        if m:
            return re.sub(r"\D", "", m.group(1))
        m = re.search(r"\b(\d{4,8})\b", self.message)
        return m.group(1) if m else None


class IprnLoginError(RuntimeError):
    """Raised when login fails — caller should NOT retry immediately."""


class IprnClient:
    def __init__(self, base_url: str, username: str, password: str, currency: str,
                 cookies_json: str = ""):
        self.base = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.currency = (currency or "EUR").upper()
        self._jar = aiohttp.CookieJar(unsafe=True)
        self._login_lock = asyncio.Lock()
        if cookies_json:
            try:
                self._load_cookies(json.loads(cookies_json))
            except Exception:
                log.warning("Failed to load saved cookies, will re-login")

    # ---------- cookie persistence ----------
    def _dump_cookies(self) -> str:
        out = []
        for c in self._jar:
            out.append({
                "key": c.key, "value": c.value,
                "domain": c["domain"] or "", "path": c["path"] or "/",
            })
        return json.dumps(out)

    def _load_cookies(self, items: list[dict]) -> None:
        from http.cookies import Morsel
        from yarl import URL
        for it in items:
            m = Morsel()
            m.set(it["key"], it["value"], it["value"])
            m["domain"] = it.get("domain") or ""
            m["path"] = it.get("path") or "/"
            self._jar.update_cookies({it["key"]: m}, response_url=URL(self.base))

    def cookies_json(self) -> str:
        return self._dump_cookies()

    # ---------- HTTP ----------
    def _session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            cookie_jar=self._jar,
            headers={
                "User-Agent": UA,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=aiohttp.ClientTimeout(total=30),
        )

    async def login(self) -> None:
        # Single-flight: only one login per client at a time.
        async with self._login_lock:
            async with self._session() as s:
                # 1) GET /login to obtain PHPSESSID + CSRF token
                async with s.get(f"{self.base}/login") as r:
                    if r.status != 200:
                        raise IprnLoginError(f"GET /login returned {r.status}")
                    html = await r.text()
                m = re.search(r'name="_csrf_token"\s+value="([^"]+)"', html)
                if not m:
                    raise IprnLoginError("CSRF token not found on /login page (panel layout changed?)")
                csrf = m.group(1)

                # 2) POST /login_check WITH csrf token (this was missing before)
                data = {
                    "_csrf_token": csrf,
                    "_username": self.username,
                    "_password": self.password,
                    "_remember_me": "on",
                    "_submit": "Login",
                }
                async with s.post(f"{self.base}/login_check", data=data,
                                  allow_redirects=True) as r:
                    final = str(r.url)
                    body = await r.text()
                    if "/login" in final and "logout" not in body.lower():
                        # Bad credentials, captcha, or rate-limit. DO NOT retry tightly.
                        raise IprnLoginError(
                            f"login rejected (still on login page) status={r.status}"
                        )
        log.info("IPRN login OK user=%s currency=%s", self.username, self.currency)

    async def fetch_sms(self) -> list[IprnRow]:
        # Last 24h range — matches the panel's default filter
        now = datetime.utcnow()
        start = now - timedelta(hours=24)
        rng = f"{start.strftime('%d/%m/%Y')} 00 - {now.strftime('%d/%m/%Y')} 23"
        params = {"currency": self.currency, "range_filter": rng}
        url = f"{self.base}/premium_number/stats/sms"
        async with self._session() as s:
            async with s.get(url, params=params, allow_redirects=False) as r:
                if r.status in (301, 302, 303):
                    raise PermissionError("session expired")
                if r.status == 404:
                    raise RuntimeError(f"endpoint 404 — base_url wrong? {url}")
                if r.status >= 500:
                    raise RuntimeError(f"server error {r.status}")
                html = await r.text()
        if "loginform" in html or "/login_check" in html:
            raise PermissionError("session expired")
        return _parse_sms_table(html)


def _parse_sms_table(html: str) -> list[IprnRow]:
    soup = BeautifulSoup(html, "html.parser")
    table = None
    for t in soup.find_all("table"):
        head = " ".join(
            (th.get_text(" ", strip=True) or "").lower() for th in t.find_all("th")
        )
        if "number" in head and ("payout" in head or "message" in head):
            table = t
            break
    if not table:
        return []
    rows: list[IprnRow] = []
    body = table.find("tbody")
    trs = body.find_all("tr") if body else table.find_all("tr")[1:]
    for tr in trs:
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(cells) < 7:
            continue
        # Source | Name | Number | CLI | Payout | Message | Notified | Created
        source, name, number, cli, payout, message, notified = cells[:7]
        created = cells[7] if len(cells) > 7 else ""
        phone = re.sub(r"\D", "", number)
        if not phone:
            continue
        rows.append(IprnRow(source=source, name=name, phone=phone, cli=cli,
                            payout=payout, message=message, notified=notified,
                            created=created))
    return rows


async def iterate_provider(client: IprnClient) -> AsyncIterator[IprnRow]:
    """Fetch SMS, transparently re-logging in once on session expiry.
    Login failures bubble up so the caller can back off (don't hammer the panel)."""
    try:
        rows = await client.fetch_sms()
    except PermissionError:
        await client.login()         # may raise IprnLoginError — don't catch here
        rows = await client.fetch_sms()
    for r in rows:
        yield r
