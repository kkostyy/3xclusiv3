# api.py — FastAPI бэкенд для Mini App 3xclusiv33

import hmac
import hashlib
import os
import logging

import aiosqlite
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/store.db")
BOT_TOKEN     = os.getenv("BOT_TOKEN", "")
ADMIN_IDS     = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()]

app = FastAPI(title="3xclusiv33 API", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Serve HTML ────────────────────────────────────────────────────────────────
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
    return {"status": "ok", "version": "3.0"}

# ── Admin check ───────────────────────────────────────────────────────────────
@app.get("/api/is_admin/{telegram_id}")
async def check_admin(telegram_id: int):
    return {"is_admin": telegram_id in ADMIN_IDS}

def require_admin(telegram_id: int):
    if telegram_id not in ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Forbidden")

# ── Products ──────────────────────────────────────────────────────────────────
@app.get("/api/products")
async def get_products():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, name, price, category, description, is_available, photo_id FROM products WHERE is_active=1 ORDER BY category, name"
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]

# ── Orders for user ───────────────────────────────────────────────────────────
@app.get("/api/orders/{telegram_id}")
async def get_orders(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT o.id, o.status, o.total_price, o.created_at, o.adjusted_price, o.adjustment_reason
               FROM orders o JOIN users u ON u.id=o.user_id
               WHERE u.telegram_id=? ORDER BY o.created_at DESC""",
            (telegram_id,),
        ) as cur:
            orders = [dict(r) for r in await cur.fetchall()]
        for o in orders:
            async with db.execute(
                "SELECT oi.qty, oi.price, p.name FROM order_items oi JOIN products p ON p.id=oi.product_id WHERE oi.order_id=?",
                (o["id"],)
            ) as cur:
                o["items"] = [dict(r) for r in await cur.fetchall()]
    return orders

# ── User profile ──────────────────────────────────────────────────────────────
@app.get("/api/user/{telegram_id}")
async def get_user(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name, language, balance FROM users WHERE telegram_id=?", (telegram_id,)) as cur:
            user = await cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        async with db.execute(
            "SELECT COUNT(*) FROM orders o JOIN users u ON u.id=o.user_id WHERE u.telegram_id=?", (telegram_id,)
        ) as cur:
            order_count = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM referrals WHERE user_id=?", (telegram_id,)) as cur:
            ref_count = (await cur.fetchone())[0]

    try:
        from config import REFERRAL_TIERS, REFERRAL_MAX_DISCOUNT
    except ImportError:
        REFERRAL_TIERS = [(1,3),(2,5),(5,10),(10,15)]
        REFERRAL_MAX_DISCOUNT = 15

    discount = 0
    for threshold, pct in REFERRAL_TIERS:
        if ref_count >= threshold:
            discount = pct
    discount = min(discount, REFERRAL_MAX_DISCOUNT)

    # Next tier
    next_tier = None
    for threshold, pct in REFERRAL_TIERS:
        if ref_count < threshold:
            next_tier = {"need": threshold - ref_count, "pct": pct}
            break

    bot_username = os.getenv("BOT_USERNAME", "xclusivv33_bot")
    return {
        "id": telegram_id, "name": user["name"], "language": user["language"],
        "balance": user["balance"], "orders": order_count, "referrals": ref_count,
        "discount": discount, "next_tier": next_tier,
        "ref_link": f"https://t.me/{bot_username}?start=ref_{telegram_id}",
    }

# ── Wishlist ──────────────────────────────────────────────────────────────────
@app.get("/api/wishlist/{telegram_id}")
async def get_wishlist(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT p.id, p.name, p.price, p.category, p.description, p.is_available, p.photo_id
               FROM wishlist w JOIN products p ON p.id=w.product_id
               WHERE w.telegram_id=?""",
            (telegram_id,)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]

class WishToggle(BaseModel):
    telegram_id: int
    product_id: int

@app.post("/api/wishlist/toggle")
async def toggle_wishlist(body: WishToggle):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id FROM wishlist WHERE telegram_id=? AND product_id=?",
            (body.telegram_id, body.product_id)
        ) as cur:
            existing = await cur.fetchone()
        if existing:
            await db.execute("DELETE FROM wishlist WHERE telegram_id=? AND product_id=?",
                           (body.telegram_id, body.product_id))
            added = False
        else:
            await db.execute("INSERT OR IGNORE INTO wishlist (telegram_id, product_id) VALUES (?,?)",
                           (body.telegram_id, body.product_id))
            added = True
        await db.commit()
    return {"added": added}

# ── Size recommendation ───────────────────────────────────────────────────────
@app.get("/api/size")
async def size_recommend(height: float, weight: float):
    SIZE_CHART = {
        "XS":  {"height": (148,158), "weight": (40,50)},
        "S":   {"height": (158,165), "weight": (48,58)},
        "M":   {"height": (165,172), "weight": (56,68)},
        "L":   {"height": (172,180), "weight": (66,80)},
        "XL":  {"height": (178,188), "weight": (78,95)},
        "XXL": {"height": (186,200), "weight": (92,130)},
    }
    scores = {}
    for size, ranges in SIZE_CHART.items():
        hmin, hmax = ranges["height"]
        wmin, wmax = ranges["weight"]
        h_score = 1 if hmin <= height <= hmax else (
            1 - min(abs(height - hmin), abs(height - hmax)) / 20)
        w_score = 1 if wmin <= weight <= wmax else (
            1 - min(abs(weight - wmin), abs(weight - wmax)) / 20)
        scores[size] = (h_score + w_score) / 2
    best = max(scores, key=scores.get)
    r = SIZE_CHART[best]
    return {
        "size": best,
        "height_range": f"{r['height'][0]}–{r['height'][1]} см",
        "weight_range": f"{r['weight'][0]}–{r['weight'][1]} кг",
    }

# ── Notifications (subscriptions) ─────────────────────────────────────────────
@app.get("/api/notifications/{telegram_id}")
async def get_notifications(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT category FROM notifications WHERE telegram_id=?", (telegram_id,)
        ) as cur:
            rows = await cur.fetchall()
    return {"subscribed": [r["category"] for r in rows]}

class NotifToggle(BaseModel):
    telegram_id: int
    category: str

@app.post("/api/notifications/toggle")
async def toggle_notification(body: NotifToggle):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id FROM notifications WHERE telegram_id=? AND category=?",
            (body.telegram_id, body.category)
        ) as cur:
            existing = await cur.fetchone()
        if existing:
            await db.execute("DELETE FROM notifications WHERE telegram_id=? AND category=?",
                           (body.telegram_id, body.category))
            subscribed = False
        else:
            await db.execute("INSERT OR IGNORE INTO notifications (telegram_id, category) VALUES (?,?)",
                           (body.telegram_id, body.category))
            subscribed = True
        await db.commit()
    return {"subscribed": subscribed}

# ── Saved addresses ───────────────────────────────────────────────────────────
@app.get("/api/addresses/{telegram_id}")
async def get_addresses(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, label, address FROM saved_addresses WHERE telegram_id=? ORDER BY id DESC",
            (telegram_id,)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]

class NewAddress(BaseModel):
    telegram_id: int
    label: str
    address: str

@app.post("/api/addresses")
async def save_address(body: NewAddress):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "INSERT INTO saved_addresses (telegram_id, label, address) VALUES (?,?,?)",
            (body.telegram_id, body.label[:30], body.address)
        )
        await db.commit()
    return {"ok": True, "id": cur.lastrowid}

@app.delete("/api/addresses/{addr_id}")
async def delete_address(addr_id: int, telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM saved_addresses WHERE id=? AND telegram_id=?", (addr_id, telegram_id))
        await db.commit()
    return {"ok": True}

# ── Checkout ──────────────────────────────────────────────────────────────────
class CheckoutBody(BaseModel):
    user_id: int
    items: list
    total: float
    name: str
    username: str
    phone: str
    address: str

@app.post("/api/checkout")
async def checkout(body: CheckoutBody):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id FROM users WHERE telegram_id=?", (body.user_id,)) as cur:
            user = await cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        cur = await db.execute(
            "INSERT INTO orders (user_id, total_price, status, customer_name, username, phone, address) VALUES (?,?,?,?,?,?,?)",
            (user["id"], body.total, "searching", body.name, body.username, body.phone, body.address)
        )
        order_id = cur.lastrowid
        for item in body.items:
            await db.execute(
                "INSERT INTO order_items (order_id, product_id, qty, price) VALUES (?,?,?,?)",
                (order_id, item["id"], item["qty"], item["price"])
            )
        await db.commit()
    return {"ok": True, "order_id": order_id}

# ── Price adjustment response ─────────────────────────────────────────────────
class PriceDecision(BaseModel):
    telegram_id: int
    action: str  # "accept" or "reject"

@app.post("/api/orders/{order_id}/price_decision")
async def price_decision(order_id: int, body: PriceDecision):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT o.*, u.telegram_id as tgid FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?",
            (order_id,)
        ) as cur:
            order = await cur.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if body.action == "accept":
            await db.execute(
                "UPDATE orders SET total_price=adjusted_price, status='ordered', adjusted_price=NULL, adjustment_reason=NULL WHERE id=?",
                (order_id,)
            )
        else:
            await db.execute(
                "UPDATE orders SET status='cancelled', adjusted_price=NULL, adjustment_reason=NULL WHERE id=?",
                (order_id,)
            )
        await db.commit()
    return {"ok": True}

# ── Reviews ───────────────────────────────────────────────────────────────────
class NewReview(BaseModel):
    telegram_id: int
    order_id: int
    rating: int
    comment: Optional[str] = ""

@app.post("/api/reviews")
async def add_review(body: NewReview):
    if not 1 <= body.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id FROM reviews WHERE telegram_id=? AND order_id=?",
            (body.telegram_id, body.order_id)
        ) as cur:
            if await cur.fetchone():
                raise HTTPException(status_code=400, detail="Already reviewed")
        await db.execute(
            "INSERT INTO reviews (telegram_id, order_id, rating, comment) VALUES (?,?,?,?)",
            (body.telegram_id, body.order_id, body.rating, body.comment)
        )
        await db.commit()
    return {"ok": True}

# ── Support (send message to admin) ──────────────────────────────────────────
class SupportMessage(BaseModel):
    telegram_id: int
    name: str
    text: str

@app.post("/api/support")
async def send_support(body: SupportMessage):
    # Store in DB for admin to see
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS support_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER, name TEXT, text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_read INTEGER DEFAULT 0)"
            )
            await db.execute(
                "INSERT INTO support_messages (telegram_id, name, text) VALUES (?,?,?)",
                (body.telegram_id, body.name, body.text)
            )
            await db.commit()
        except Exception:
            pass
    return {"ok": True}

# ═════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ═════════════════════════════════════════════════════════════

@app.get("/api/admin/orders")
async def admin_get_orders(admin_id: int = 0):
    require_admin(admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT o.id, o.status, o.total_price, o.created_at,
                      o.customer_name, o.username, o.phone, o.address,
                      o.adjusted_price, o.adjustment_reason,
                      u.telegram_id, u.name as user_name
               FROM orders o JOIN users u ON u.id=o.user_id
               ORDER BY o.created_at DESC"""
        ) as cur:
            orders = [dict(r) for r in await cur.fetchall()]
        for order in orders:
            async with db.execute(
                "SELECT oi.qty, oi.price, p.name FROM order_items oi JOIN products p ON p.id=oi.product_id WHERE oi.order_id=?",
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
    valid = ["searching","ordered","in_transit","arrived","delivered","cancelled"]
    if body.status not in valid:
        raise HTTPException(status_code=400, detail="Invalid status")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE orders SET status=? WHERE id=?", (body.status, order_id))
        await db.commit()
    return {"ok": True}

class PriceAdjust(BaseModel):
    admin_id: int
    new_price: float
    reason: str

@app.post("/api/admin/orders/{order_id}/adjust_price")
async def admin_adjust_price(order_id: int, body: PriceAdjust):
    require_admin(body.admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE orders SET adjusted_price=?, adjustment_reason=? WHERE id=?",
            (body.new_price, body.reason, order_id)
        )
        await db.commit()
    return {"ok": True}

@app.get("/api/admin/products")
async def admin_get_products(admin_id: int = 0):
    require_admin(admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, name, price, category, description, is_available, photo_id FROM products WHERE is_active=1 ORDER BY category, name"
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
            raise HTTPException(status_code=404, detail="Not found")
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

class DeleteProduct(BaseModel):
    admin_id: int

@app.delete("/api/admin/products/{product_id}")
async def admin_delete_product(product_id: int, admin_id: int = 0):
    require_admin(admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE products SET is_active=0 WHERE id=?", (product_id,))
        await db.commit()
    return {"ok": True}

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
        async with db.execute("SELECT COUNT(*) as cnt FROM orders") as c:
            total_orders = (await c.fetchone())["cnt"]
        async with db.execute(
            """SELECT p.name, p.category, COALESCE(SUM(oi.qty),0) as sold, COALESCE(SUM(oi.qty*oi.price),0) as revenue
               FROM products p LEFT JOIN order_items oi ON oi.product_id=p.id
               LEFT JOIN orders o ON o.id=oi.order_id AND o.status='delivered'
               WHERE p.is_active=1 GROUP BY p.id ORDER BY sold DESC LIMIT 5"""
        ) as c:
            top_products = [dict(r) for r in await c.fetchall()]
        async with db.execute(
            """SELECT AVG(rating) as avg_rating, COUNT(*) as cnt FROM reviews"""
        ) as c:
            reviews_row = await c.fetchone()
    return {
        "new_orders": new_orders,
        "active_orders": active_orders,
        "total_orders": total_orders,
        "revenue": revenue,
        "users": users,
        "top_products": top_products,
        "avg_rating": round(reviews_row["avg_rating"] or 0, 1),
        "reviews_count": reviews_row["cnt"],
    }

@app.get("/api/admin/reviews")
async def admin_get_reviews(admin_id: int = 0):
    require_admin(admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT r.*, u.name as user_name FROM reviews r JOIN users u ON u.telegram_id=r.telegram_id ORDER BY r.created_at DESC LIMIT 50"
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]

@app.get("/api/admin/support")
async def admin_get_support(admin_id: int = 0):
    require_admin(admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute(
                "SELECT * FROM support_messages ORDER BY created_at DESC LIMIT 100"
            ) as cur:
                return [dict(r) for r in await cur.fetchall()]
        except Exception:
            return []


# ── Categories ────────────────────────────────────────────────────────────────
@app.get("/api/categories")
async def get_categories():
    """Return all product categories (built-in + custom)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            async with db.execute("SELECT id, label, glyph FROM categories ORDER BY sort_order") as cur:
                rows = await cur.fetchall()
            if rows:
                return [{"id": r[0], "label": r[1], "glyph": r[2]} for r in rows]
        except Exception:
            pass
    # Fallback: built-in categories
    return [
        {"id": "clothes",     "label": "Одежда",     "glyph": "👕"},
        {"id": "shoes",       "label": "Обувь",       "glyph": "👟"},
        {"id": "accessories", "label": "Аксессуары", "glyph": "👜"},
    ]

class NewCategory(BaseModel):
    admin_id: int
    id: str
    label: str
    glyph: Optional[str] = "✦"

@app.post("/api/admin/categories")
async def admin_add_category(body: NewCategory):
    require_admin(body.admin_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                glyph TEXT DEFAULT '✦',
                sort_order INTEGER DEFAULT 100
            )
        """)
        # Get max sort order
        async with db.execute("SELECT COUNT(*) FROM categories") as cur:
            count = (await cur.fetchone())[0]
        await db.execute(
            "INSERT OR REPLACE INTO categories (id, label, glyph, sort_order) VALUES (?,?,?,?)",
            (body.id, body.label, body.glyph, count + 10)
        )
        await db.commit()
    return {"ok": True}

@app.delete("/api/admin/categories/{category_id}")
async def admin_delete_category(category_id: str, admin_id: int = 0):
    require_admin(admin_id)
    built_in = {"clothes", "shoes", "accessories"}
    if category_id in built_in:
        raise HTTPException(status_code=400, detail="Cannot delete built-in category")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM categories WHERE id=?", (category_id,))
        await db.commit()
    return {"ok": True}

# ── Photo proxy ───────────────────────────────────────────────────────────────
from fastapi.responses import Response
import asyncio
import urllib.request

@app.get("/api/photo/{file_id:path}")
async def proxy_photo(file_id: str):
    """Proxy Telegram photo by file_id → actual image bytes (no httpx needed)."""
    if not BOT_TOKEN:
        raise HTTPException(status_code=503, detail="No bot token")
    try:
        def fetch_sync():
            # 1. Get file path
            with urllib.request.urlopen(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}",
                timeout=10
            ) as r:
                import json
                data = json.loads(r.read())
            if not data.get("ok"):
                return None, None
            file_path = data["result"]["file_path"]
            # 2. Download image
            with urllib.request.urlopen(
                f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}",
                timeout=10
            ) as r:
                img_bytes = r.read()
            content_type = "image/jpeg"
            if file_path.endswith(".png"): content_type = "image/png"
            elif file_path.endswith(".webp"): content_type = "image/webp"
            return img_bytes, content_type

        img_bytes, content_type = await asyncio.get_event_loop().run_in_executor(None, fetch_sync)
        if img_bytes is None:
            raise HTTPException(status_code=404, detail="File not found")
        return Response(content=img_bytes, media_type=content_type,
                       headers={"Cache-Control": "public, max-age=86400"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
