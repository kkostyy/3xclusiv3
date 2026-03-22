# api.py — FastAPI бэкенд для Mini App 3xclusiv33

import hmac
import hashlib
import os
import logging

import aiosqlite
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/store.db")
BOT_TOKEN     = os.getenv("BOT_TOKEN", "")
ADMIN_IDS     = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()]

app = FastAPI(title="3xclusiv33 API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/", response_class=HTMLResponse)
async def serve_miniapp():
    try: return open("miniapp.html", encoding="utf-8").read()
    except FileNotFoundError: return "<h1>miniapp.html not found</h1>"

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    try: return open("admin.html", encoding="utf-8").read()
    except FileNotFoundError: return "<h1>admin.html not found</h1>"

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/is_admin/{telegram_id}")
async def check_admin(telegram_id: int):
    return {"is_admin": telegram_id in ADMIN_IDS}

@app.get("/api/products")
async def get_products():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, name, price, category, description, is_available FROM products WHERE is_active = 1 ORDER BY category, name"
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]

@app.get("/api/orders/{telegram_id}")
async def get_orders(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT o.id, o.status, o.total_price, o.created_at
               FROM orders o JOIN users u ON u.id = o.user_id
               WHERE u.telegram_id = ? ORDER BY o.created_at DESC""",
            (telegram_id,),
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]

@app.get("/api/user/{telegram_id}")
async def get_user(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name, language, balance FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
            user = await cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        async with db.execute(
            "SELECT COUNT(*) FROM orders o JOIN users u ON u.id = o.user_id WHERE u.telegram_id = ?", (telegram_id,)
        ) as cur:
            order_count = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM referrals WHERE user_id = ?", (telegram_id,)) as cur:
            ref_count = (await cur.fetchone())[0]

    try:
        from config import REFERRAL_TIERS, REFERRAL_MAX_DISCOUNT
    except ImportError:
        REFERRAL_TIERS = [(1, 3), (3, 5), (5, 10)]
        REFERRAL_MAX_DISCOUNT = 15

    discount = 0
    for threshold, pct in REFERRAL_TIERS:
        if ref_count >= threshold:
            discount = pct
    discount = min(discount, REFERRAL_MAX_DISCOUNT)
    bot_username = os.getenv("BOT_USERNAME", "your_bot")
    return {
        "id": telegram_id, "name": user["name"], "language": user["language"],
        "balance": user["balance"], "orders": order_count, "referrals": ref_count,
        "discount": discount, "ref_link": f"https://t.me/{bot_username}?start=ref_{telegram_id}",
    }

@app.post("/api/checkout")
async def receive_checkout(request: Request):
    body = await request.json()
    logger.info("Checkout from user %s", body.get("user_id"))
    return {"ok": True}

# ══════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ══════════════════════════════════════════════════════════════

def require_admin(telegram_id: int):
    if telegram_id not in ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.get("/api/admin/orders")
async def admin_get_orders(admin_id: int = 0):
    require_admin(admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT o.id, o.status, o.total_price, o.created_at,
                      o.customer_name, o.username, o.phone, o.address,
                      u.telegram_id, u.name as user_name
               FROM orders o JOIN users u ON u.id = o.user_id
               ORDER BY o.created_at DESC"""
        ) as cur:
            orders = [dict(r) for r in await cur.fetchall()]
        for order in orders:
            async with db.execute(
                """SELECT oi.qty, oi.price, p.name FROM order_items oi
                   JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ?""",
                (order["id"],)
            ) as cur:
                order["items"] = [dict(r) for r in await cur.fetchall()]
            order["tg"] = f"@{order['username']}" if order.get("username") else f"id{order.get('telegram_id','')}"
    return orders

class StatusUpdate(BaseModel):
    status: str
    admin_id: int

@app.patch("/api/admin/orders/{order_id}")
async def admin_update_status(order_id: int, body: StatusUpdate):
    require_admin(body.admin_id)
    valid = ["searching", "ordered", "in_transit", "arrived", "delivered", "cancelled"]
    if body.status not in valid:
        raise HTTPException(status_code=400, detail="Invalid status")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE orders SET status=? WHERE id=?", (body.status, order_id))
        await db.commit()
    return {"ok": True}

@app.get("/api/admin/products")
async def admin_get_products(admin_id: int = 0):
    require_admin(admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, name, price, category, description, is_available FROM products WHERE is_active=1 ORDER BY category, name"
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]

class ToggleAvail(BaseModel):
    admin_id: int

@app.patch("/api/admin/products/{product_id}/toggle")
async def admin_toggle_product(product_id: int, body: ToggleAvail):
    require_admin(body.admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT is_available FROM products WHERE id=?", (product_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        new_val = 0 if row[0] else 1
        await db.execute("UPDATE products SET is_available=? WHERE id=?", (new_val, product_id))
        await db.commit()
    return {"ok": True, "is_available": new_val}

class NewProduct(BaseModel):
    admin_id: int
    name: str
    price: float
    category: str
    description: Optional[str] = ""

@app.post("/api/admin/products")
async def admin_add_product(body: NewProduct):
    require_admin(body.admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "INSERT INTO products (name, price, category, description, is_available, is_active) VALUES (?,?,?,?,1,1)",
            (body.name, body.price, body.category, body.description)
        )
        await db.commit()
    return {"ok": True, "id": cur.lastrowid}

@app.get("/api/admin/stats")
async def admin_stats(admin_id: int = 0):
    require_admin(admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) as cnt FROM orders WHERE status='searching'") as c:
            new_orders = (await c.fetchone())["cnt"]
        async with db.execute("SELECT COUNT(*) as cnt FROM orders WHERE status NOT IN ('delivered','cancelled')") as c:
            active_orders = (await c.fetchone())["cnt"]
        async with db.execute("SELECT COALESCE(SUM(total_price),0) as rev FROM orders WHERE status='delivered'") as c:
            revenue = (await c.fetchone())["rev"]
        async with db.execute("SELECT COUNT(*) as cnt FROM users") as c:
            users = (await c.fetchone())["cnt"]
    return {"new_orders": new_orders, "active_orders": active_orders, "revenue": revenue, "users": users}
