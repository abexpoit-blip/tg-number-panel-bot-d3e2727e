"""IPRN-SMS panel scraper.

Logs in, persists cookies, polls /premium_number/stats/sms?currency=XXX,
parses the SMS table, and yields parsed OTP rows (phone, code, raw, service hint).

The page returns a Bootstrap data-table. We post the same form the UI submits
(currency + range_filter + search) and parse <table> rows server-side rendered.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import AsyncIterator

import aiohttp
from bs4 import BeautifulSoup

log = logging.getLogger("scraper.iprn")

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


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
        # Common OTP patterns in IPRN messages
        m = re.search(r"\b(\d{3}[- ]?\d{3,4})\b", self.message)
        if m:
            return re.sub(r"\D", "", m.group(1))
        m = re.search(r"\b(\d{4,8})\b", self.message)
        return m.group(1) if m else None


class IprnClient:
    def __init__(self, base_url: str, username: str, password: str, currency: str,
                 cookies_json: str = ""):
        self.base = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.currency = (currency or "EUR").upper()
        self._jar = aiohttp.CookieJar(unsafe=True)
        if cookies_json:
            try:
                self._load_cookies(json.loads(cookies_json))
            except Exception:
                pass

    # ---------- cookie persistence ----------
    def _dump_cookies(self) -> str:
        out = []
        for c in self._jar:
            out.append({"key": c.key, "value": c.value, "domain": c["domain"] or "", "path": c["path"] or "/"})
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
            headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
            timeout=aiohttp.ClientTimeout(total=30),
        )

    async def login(self) -> None:
        async with self._session() as s:
            # GET login to obtain session cookie
            await s.get(f"{self.base}/login")
            data = {"_username": self.username, "_password": self.password, "_remember_me": "on"}
            async with s.post(f"{self.base}/login_check", data=data, allow_redirects=True) as r:
                final = str(r.url)
                body = await r.text()
                if "/login" in final and "logout" not in body.lower():
                    raise RuntimeError(f"IPRN login failed (still on login page) status={r.status}")
        log.info("IPRN login OK for %s (%s)", self.username, self.currency)

    async def fetch_sms(self) -> list[IprnRow]:
        # Last 24h range
        now = datetime.utcnow()
        start = now - timedelta(hours=24)
        rng = f"{start.strftime('%d/%m/%Y')} 00 - {now.strftime('%d/%m/%Y')} 23"
        params = {"currency": self.currency, "range_filter": rng}
        url = f"{self.base}/premium_number/stats/sms"
        async with self._session() as s:
            async with s.get(url, params=params, allow_redirects=False) as r:
                if r.status in (301, 302, 303):
                    raise PermissionError("session expired")
                html = await r.text()
        if "loginform" in html or "/login_check" in html:
            raise PermissionError("session expired")
        return _parse_sms_table(html)


def _parse_sms_table(html: str) -> list[IprnRow]:
    soup = BeautifulSoup(html, "html.parser")
    table = None
    for t in soup.find_all("table"):
        head = " ".join((th.get_text(" ", strip=True) or "").lower() for th in t.find_all("th"))
        if "number" in head and ("payout" in head or "message" in head):
            table = t
            break
    if not table:
        return []
    rows: list[IprnRow] = []
    for tr in table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")[1:]:
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
                            payout=payout, message=message, notified=notified, created=created))
    return rows


async def iterate_provider(client: IprnClient) -> AsyncIterator[IprnRow]:
    """Convenience helper: re-login on session expiry, yield rows."""
    try:
        rows = await client.fetch_sms()
    except PermissionError:
        await client.login()
        rows = await client.fetch_sms()
    for r in rows:
        yield r
