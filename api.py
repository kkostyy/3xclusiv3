# api.py — FastAPI бэкенд для Mini App 3xclusiv33
# Деплоится на Railway/Render/VPS вместе с ботом

import hmac
import hashlib
import os
import logging

import aiosqlite
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/store.db")
BOT_TOKEN     = os.getenv("BOT_TOKEN", "")


# ── Telegram initData validation ──────────────────────────────────────────────
def validate_init_data(init_data: str) -> bool:
    """Проверяет, что запрос действительно пришёл от Telegram."""
    if not BOT_TOKEN or not init_data:
        return False
    try:
        vals       = dict(p.split("=", 1) for p in init_data.split("&") if "=" in p)
        check_hash = vals.pop("hash", "")
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(vals.items()))
        secret     = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc       = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(calc, check_hash)
    except Exception:
        return False


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="3xclusiv33 API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # В продакшне замените на ваш домен Vercel
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Serve Mini App ────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_miniapp():
    """Отдаёт miniapp.html. На Vercel — это статичный файл, здесь — fallback."""
    try:
        return open("miniapp.html", encoding="utf-8").read()
    except FileNotFoundError:
        return "<h1>miniapp.html not found</h1><p>Deploy miniapp.html alongside api.py</p>"


# ── Products ──────────────────────────────────────────────────────────────────
@app.get("/api/products")
async def get_products():
    """Возвращает все активные товары, отсортированные по категории."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT id, name, price, category, description, is_available
               FROM products
               WHERE is_active = 1
               ORDER BY category, name"""
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


# ── Orders for user ───────────────────────────────────────────────────────────
@app.get("/api/orders/{telegram_id}")
async def get_orders(telegram_id: int):
    """Возвращает заказы пользователя по его Telegram ID."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT o.id, o.status, o.total_price, o.created_at
               FROM orders o
               JOIN users u ON u.id = o.user_id
               WHERE u.telegram_id = ?
               ORDER BY o.created_at DESC""",
            (telegram_id,),
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


# ── User profile ──────────────────────────────────────────────────────────────
@app.get("/api/user/{telegram_id}")
async def get_user(telegram_id: int):
    """Возвращает профиль пользователя: статистику, скидку, реферальную ссылку."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT id, name, language, balance FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ) as cur:
            user = await cur.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        async with db.execute(
            """SELECT COUNT(*) FROM orders o
               JOIN users u ON u.id = o.user_id
               WHERE u.telegram_id = ?""",
            (telegram_id,),
        ) as cur:
            order_count = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM referrals WHERE user_id = ?",
            (telegram_id,),
        ) as cur:
            ref_count = (await cur.fetchone())[0]

    # Расчёт скидки по реферальным уровням
    try:
        from config import REFERRAL_TIERS, REFERRAL_MAX_DISCOUNT
    except ImportError:
        REFERRAL_TIERS      = [(1, 3), (3, 5), (5, 10)]
        REFERRAL_MAX_DISCOUNT = 15

    discount = 0
    for threshold, pct in REFERRAL_TIERS:
        if ref_count >= threshold:
            discount = pct
    discount = min(discount, REFERRAL_MAX_DISCOUNT)

    bot_username = os.getenv("BOT_USERNAME", "your_bot")
    return {
        "id":        telegram_id,
        "name":      user["name"],
        "language":  user["language"],
        "balance":   user["balance"],
        "orders":    order_count,
        "referrals": ref_count,
        "discount":  discount,
        "ref_link":  f"https://t.me/{bot_username}?start=ref_{telegram_id}",
    }


# ── Receive cart from Mini App ────────────────────────────────────────────────
@app.post("/api/checkout")
async def receive_checkout(request: Request):
    """
    Принимает данные корзины из Mini App.
    Telegram сам передаёт sendData() в бот через webhook — этот endpoint
    является дополнительным каналом для веб-интеграции вне Telegram.
    """
    body = await request.json()
    user_id = body.get("user_id")
    items   = body.get("items", [])
    total   = body.get("total", 0)

    logger.info("Checkout from user %s: %d items, total %.2f", user_id, len(items), total)
    # Здесь можно создавать заказ в БД напрямую, если нужно
    return {"ok": True, "message": "Order received"}


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "3xclusiv33", "version": "2.0"}
