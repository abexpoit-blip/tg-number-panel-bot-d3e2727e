# Seven1tel TG Number Panel — Self-Hosted Stack

Full-stack Telegram number panel with admin web UI. Runs entirely in Docker on a VPS.

## Stack

- **postgres** — database
- **api** — FastAPI backend (auth, services, countries, numbers, users, OTPs)
- **bot** — aiogram Telegram bot (user menu + OTP feed listener in one process)
- **admin-panel** — React + Vite SPA, served by nginx
- **nginx** — reverse proxy at `tg.nexus-x.site`

## Quick deploy on a fresh VPS

```bash
# 1. Clone
cd /opt
git clone https://github.com/abexpoit-blip/tg-number-panel-bot-d3e2727e.git tg-number-panel-bot
cd tg-number-panel-bot

# 2. Configure environment
cp .env.example .env
nano .env   # set BOT_TOKEN, OTP_FEED_CHANNEL_ID, ADMIN_CHAT_ID, strong passwords

# 3. Build & start
docker compose up -d --build

# 4. Tail logs
docker compose logs -f api bot
```

The host nginx (or any reverse proxy) should forward `tg.nexus-x.site` → `127.0.0.1:8088`.

## Required `.env` values

| Variable | Example | Notes |
|---|---|---|
| `POSTGRES_PASSWORD` | `openssl rand -hex 24` | Strong random |
| `JWT_SECRET` | `openssl rand -hex 32` | Strong random |
| `ADMIN_EMAIL` | `admin@seven1tel.com` | Admin panel login |
| `ADMIN_PASSWORD` | `Shovon@5448` | Admin panel login |
| `BOT_TOKEN` | `123456:ABC...` | From @BotFather |
| `ADMIN_CHAT_ID` | `5311644406` | Your Telegram user ID |
| `OTP_FEED_CHANNEL_ID` | `-1003726383667` | Channel the bot is a member of |

## How OTP delivery works

1. Bot is added as a **member** of the OTP feed channel (`OTP_FEED_CHANNEL_ID`).
2. Channel posts arrive via `channel_post` updates.
3. `parser.py` extracts: `phone` (longest digit run ≥ 8), `service_hint` (FACEBOOK / WHATSAPP / …), and `code` (preferred from inline `copy_text` button, fallback regex on text).
4. Bot looks up the matching `numbers.phone` row.
5. If a user is assigned → bot DMs them with a copy button formatted `+phone|otp`.
6. Every parse is logged to the `otps` table (visible in admin → Live OTP).

## Admin panel pages

- **Dashboard** — counts of numbers / users / OTPs
- **Services** — manage WhatsApp / Facebook / Instagram / Telegram / TikTok …
- **Countries** — flags, ISO, dial codes
- **Numbers** — bulk upload phones (one per line) per service+country
- **Users** — Telegram users, adjust balance, ban/unban
- **Live OTP** — last 200 OTPs received (matched & unmatched)
- **Settings** — key/value store for bot copy

## Bot commands & menu

`/start` opens the keyboard:
- 🤖 Get Number — pick service → country → bot assigns 5 available numbers, each with copy button
- 💰 Balance — cosmetic, service is free
- 📊 Status — your active numbers + OTPs received
- 🌍 Available Country — full country list

When an OTP arrives for one of your numbers, the bot DMs you immediately with a copy button containing `+phone|otp`.

## Updating

```bash
cd /opt/tg-number-panel-bot
git pull
docker compose up -d --build
```

## Backups

```bash
docker compose exec db pg_dump -U panel panel | gzip > backup-$(date +%F).sql.gz
```
