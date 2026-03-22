# 3xclusiv33 — Telegram Mini App

Fashion store bot + Mini App.

## Deploy on Railway

1. Fork/push this repo to GitHub (files must be in **root**, not in a subfolder)
2. Connect Railway → New Project → Deploy from GitHub
3. Add Variables:
   - `BOT_TOKEN` — your bot token from @BotFather
   - `ADMIN_IDS` — your Telegram ID (comma-separated)
   - `DATABASE_PATH` — `data/store.db`
   - `PORT` — `8080`
4. Railway will auto-detect Python via `requirements.txt` and run `Procfile`

## Deploy miniapp.html + admin.html on Vercel

Upload only `miniapp.html`, `admin.html`, `vercel.json` to a separate repo → deploy on vercel.com

See `GUIDE.html` for full instructions.
