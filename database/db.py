import aiosqlite, os, logging
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

def _p():
    dir_name = os.path.dirname(DATABASE_PATH)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    return DATABASE_PATH

async def init_db():
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                name TEXT, language TEXT DEFAULT 'ru',
                referral_id INTEGER, balance REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, price REAL NOT NULL,
                category TEXT NOT NULL, description TEXT,
                photo_id TEXT, is_active INTEGER DEFAULT 1,
                is_available INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, status TEXT DEFAULT 'searching',
                total_price REAL NOT NULL,
                adjusted_price REAL DEFAULT NULL,
                adjustment_reason TEXT DEFAULT NULL,
                customer_name TEXT, tg_username TEXT,
                phone TEXT, address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1, price REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, invited_user_id INTEGER NOT NULL,
                bonus_paid INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, order_id INTEGER NOT NULL,
                rating INTEGER NOT NULL, comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS qc_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL, photo_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                UNIQUE(telegram_id, category)
            );
            CREATE TABLE IF NOT EXISTS wishlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(telegram_id, product_id)
            );
            CREATE TABLE IF NOT EXISTS saved_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL, discount REAL NOT NULL,
                uses_left INTEGER DEFAULT 1, is_active INTEGER DEFAULT 1
            );
        """)
        await db.commit()
    logger.info("DB ready: %s", DATABASE_PATH)

async def migrate_db():
    """Migration: add new tables if they do not exist."""
    async with aiosqlite.connect(_p()) as db:
        # tg_username in orders
        try:
            await db.execute("ALTER TABLE orders ADD COLUMN tg_username TEXT")
            await db.commit()
        except Exception:
            pass
        # is_available column for stop-list
        try:
            await db.execute("ALTER TABLE products ADD COLUMN is_available INTEGER DEFAULT 1")
            await db.commit()
        except Exception:
            pass
        # price adjustment columns
        for col in ["adjusted_price REAL DEFAULT NULL", "adjustment_reason TEXT DEFAULT NULL"]:
            try:
                await db.execute(f"ALTER TABLE orders ADD COLUMN {col}")
                await db.commit()
            except Exception:
                pass
        # New tables (safe — CREATE IF NOT EXISTS)
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                UNIQUE(telegram_id, category)
            );
            CREATE TABLE IF NOT EXISTS wishlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(telegram_id, product_id)
            );
            CREATE TABLE IF NOT EXISTS saved_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()
        logger.info("Migration complete")

# ── USERS ──
async def get_user(tid: int):
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)) as c:
            return await c.fetchone()

async def create_user(tid: int, name: str, lang: str="ru", ref_id=None):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("INSERT OR IGNORE INTO users(telegram_id,name,language,referral_id) VALUES(?,?,?,?)",
                         (tid, name, lang, ref_id))
        await db.commit()

async def update_user_language(tid: int, lang: str):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("UPDATE users SET language=? WHERE telegram_id=?", (lang, tid))
        await db.commit()

async def update_user_balance(tid: int, delta: float):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("UPDATE users SET balance=balance+? WHERE telegram_id=?", (delta, tid))
        await db.commit()

async def get_user_language(tid: int) -> str:
    u = await get_user(tid)
    return u["language"] if u else "ru"

async def count_user_orders(tid: int) -> int:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT COUNT(*) FROM orders o JOIN users u ON u.id=o.user_id WHERE u.telegram_id=?", (tid,)
        ) as c:
            r = await c.fetchone(); return r[0] if r else 0

async def get_all_users() -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as c:
            return await c.fetchall()

# ── PRODUCTS ──
async def get_products_by_category(cat: str) -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE category=? AND is_active=1 AND is_available=1", (cat,)) as c:
            return await c.fetchall()

async def get_all_products() -> list:
    """All active products including unavailable (for admin)."""
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE is_active=1 ORDER BY is_available DESC, name") as c:
            return await c.fetchall()

async def get_available_products() -> list:
    """Only in-stock products (for buyers)."""
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE is_active=1 AND is_available=1") as c:
            return await c.fetchall()

async def get_product(pid: int):
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE id=?", (pid,)) as c:
            return await c.fetchone()

async def add_product(name, price, cat, desc, photo_id) -> int:
    async with aiosqlite.connect(_p()) as db:
        c = await db.execute("INSERT INTO products(name,price,category,description,photo_id) VALUES(?,?,?,?,?)",
                             (name, price, cat, desc, photo_id))
        await db.commit(); return c.lastrowid

async def update_product(pid, name, price, desc, photo_id):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("UPDATE products SET name=?,price=?,description=?,photo_id=? WHERE id=?",
                         (name, price, desc, photo_id, pid))
        await db.commit()

async def delete_product(pid: int):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("UPDATE products SET is_active=0 WHERE id=?", (pid,))
        await db.commit()

async def toggle_product_availability(pid: int) -> bool:
    """Toggle is_available. Returns new state: True=available, False=out of stock."""
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT is_available FROM products WHERE id=?", (pid,)) as c:
            row = await c.fetchone()
        if not row:
            return False
        new_val = 0 if row["is_available"] else 1
        await db.execute("UPDATE products SET is_available=? WHERE id=?", (new_val, pid))
        await db.commit()
        return bool(new_val)

# ── ORDERS ──
async def create_order(tid, total, cname, username, phone, address) -> int:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id FROM users WHERE telegram_id=?", (tid,)) as c:
            row = await c.fetchone()
        if not row:
            await db.execute(
                "INSERT OR IGNORE INTO users(telegram_id, name, language) VALUES(?, ?, ?)",
                (tid, f"User_{tid}", "ru")
            )
            await db.commit()
            async with db.execute("SELECT id FROM users WHERE telegram_id=?", (tid,)) as c:
                row = await c.fetchone()
        uid = row["id"]
        c = await db.execute(
            "INSERT INTO orders(user_id,total_price,customer_name,tg_username,phone,address) VALUES(?,?,?,?,?,?)",
            (uid, total, cname, username, phone, address)
        )
        await db.commit()
        return c.lastrowid

async def add_order_item(order_id, product_id, qty, price):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("INSERT INTO order_items(order_id,product_id,quantity,price) VALUES(?,?,?,?)",
                         (order_id, product_id, qty, price))
        await db.commit()

async def get_order(oid: int):
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT o.*,u.telegram_id FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?", (oid,)
        ) as c: return await c.fetchone()

async def get_user_orders(tid: int) -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT o.* FROM orders o JOIN users u ON u.id=o.user_id WHERE u.telegram_id=? ORDER BY o.created_at DESC", (tid,)
        ) as c: return await c.fetchall()

async def get_all_orders() -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT o.*,u.telegram_id,u.name as uname FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC"
        ) as c: return await c.fetchall()

async def get_order_items(oid: int) -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT oi.*,p.name FROM order_items oi JOIN products p ON p.id=oi.product_id WHERE oi.order_id=?", (oid,)
        ) as c: return await c.fetchall()

async def update_order_status(oid: int, status: str):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
        await db.commit()

# ── REFERRALS ──
async def create_referral(ref_tid, inv_tid):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("INSERT OR IGNORE INTO referrals(user_id,invited_user_id) VALUES(?,?)", (ref_tid, inv_tid))
        await db.commit()

async def get_all_referrals() -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM referrals ORDER BY created_at DESC") as c:
            return await c.fetchall()

async def get_unpaid_referral(inv_tid: int):
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM referrals WHERE invited_user_id=? AND bonus_paid=0", (inv_tid,)
        ) as c: return await c.fetchone()

async def mark_referral_bonus_paid(ref_tid, inv_tid):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("UPDATE referrals SET bonus_paid=1 WHERE user_id=? AND invited_user_id=?", (ref_tid, inv_tid))
        await db.commit()

# ── REVIEWS ──
async def add_review(tid, oid, rating, comment):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("INSERT INTO reviews(user_id,order_id,rating,comment) VALUES(?,?,?,?)",
                         (tid, oid, rating, comment))
        await db.commit()

async def get_all_reviews() -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT r.*,u.telegram_id,u.name as uname FROM reviews r JOIN users u ON u.id=r.user_id ORDER BY r.created_at DESC"
        ) as c: return await c.fetchall()

async def has_reviewed(tid, oid) -> bool:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id FROM reviews WHERE user_id=? AND order_id=?", (tid, oid)
        ) as c: return await c.fetchone() is not None

# ── QC ──
async def create_qc_request(oid, photo_id) -> int:
    async with aiosqlite.connect(_p()) as db:
        c = await db.execute("INSERT INTO qc_requests(order_id,photo_id) VALUES(?,?)", (oid, photo_id))
        await db.commit(); return c.lastrowid

async def get_qc_request(qid: int):
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM qc_requests WHERE id=?", (qid,)) as c:
            return await c.fetchone()

async def update_qc_status(qid, status):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("UPDATE qc_requests SET status=? WHERE id=?", (status, qid))
        await db.commit()

# ── STATS ──
async def get_stats() -> dict:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) as c FROM users") as cur:
            users = (await cur.fetchone())["c"]
        async with db.execute("SELECT COUNT(*) as c FROM orders") as cur:
            orders = (await cur.fetchone())["c"]
        async with db.execute("SELECT COALESCE(SUM(total_price),0) as s FROM orders WHERE status='delivered'") as cur:
            revenue = (await cur.fetchone())["s"]
        async with db.execute("SELECT COUNT(*) as c FROM orders WHERE status='searching'") as cur:
            pending = (await cur.fetchone())["c"]
    return {"users": users, "orders": orders, "revenue": revenue, "pending": pending}

async def count_referrals(referrer_tg_id: int) -> int:
    async with aiosqlite.connect(_p()) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM referrals WHERE user_id=?", (referrer_tg_id,)
        ) as c:
            r = await c.fetchone()
            return r[0] if r else 0

# ── PRICE ADJUSTMENT ──
async def set_price_adjustment(oid: int, adjusted_price: float, reason: str):
    async with aiosqlite.connect(_p()) as db:
        await db.execute(
            "UPDATE orders SET adjusted_price=?, adjustment_reason=?, status='ordered' WHERE id=?",
            (adjusted_price, reason, oid)
        )
        await db.commit()

async def accept_price_adjustment(oid: int):
    """Buyer accepted the adjusted price — move to ordered."""
    async with aiosqlite.connect(_p()) as db:
        await db.execute(
            "UPDATE orders SET status='ordered' WHERE id=?", (oid,)
        )
        await db.commit()

async def reject_price_adjustment(oid: int):
    """Buyer rejected — cancel order."""
    async with aiosqlite.connect(_p()) as db:
        await db.execute(
            "UPDATE orders SET status='cancelled', adjusted_price=NULL, adjustment_reason=NULL WHERE id=?",
            (oid,)
        )
        await db.commit()

# ── NOTIFICATIONS ──
async def toggle_notification(tid: int, category: str) -> bool:
    """Toggle subscription. Returns True if subscribed, False if unsubscribed."""
    async with aiosqlite.connect(_p()) as db:
        async with db.execute(
            "SELECT id FROM notifications WHERE telegram_id=? AND category=?", (tid, category)
        ) as c:
            row = await c.fetchone()
        if row:
            await db.execute("DELETE FROM notifications WHERE telegram_id=? AND category=?", (tid, category))
            await db.commit()
            return False
        else:
            await db.execute("INSERT OR IGNORE INTO notifications(telegram_id, category) VALUES(?,?)", (tid, category))
            await db.commit()
            return True

async def get_user_notifications(tid: int) -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT category FROM notifications WHERE telegram_id=?", (tid,)) as c:
            return [r["category"] for r in await c.fetchall()]

async def get_subscribers_for_category(category: str) -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT telegram_id FROM notifications WHERE category=?", (category,)) as c:
            return [r["telegram_id"] for r in await c.fetchall()]

# ── WISHLIST ──
async def toggle_wishlist(tid: int, pid: int) -> bool:
    """Toggle product in wishlist. Returns True if added, False if removed."""
    async with aiosqlite.connect(_p()) as db:
        async with db.execute(
            "SELECT id FROM wishlist WHERE telegram_id=? AND product_id=?", (tid, pid)
        ) as c:
            row = await c.fetchone()
        if row:
            await db.execute("DELETE FROM wishlist WHERE telegram_id=? AND product_id=?", (tid, pid))
            await db.commit()
            return False
        else:
            await db.execute("INSERT OR IGNORE INTO wishlist(telegram_id, product_id) VALUES(?,?)", (tid, pid))
            await db.commit()
            return True

async def get_wishlist(tid: int) -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT p.* FROM wishlist w
               JOIN products p ON p.id = w.product_id
               WHERE w.telegram_id=? AND p.is_active=1
               ORDER BY w.created_at DESC""", (tid,)
        ) as c:
            return await c.fetchall()

async def is_in_wishlist(tid: int, pid: int) -> bool:
    async with aiosqlite.connect(_p()) as db:
        async with db.execute(
            "SELECT id FROM wishlist WHERE telegram_id=? AND product_id=?", (tid, pid)
        ) as c:
            return await c.fetchone() is not None

# ── SAVED ADDRESSES ──
async def get_saved_addresses(tid: int) -> list:
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM saved_addresses WHERE telegram_id=? ORDER BY created_at DESC LIMIT 5", (tid,)
        ) as c:
            return await c.fetchall()

async def save_address(tid: int, label: str, address: str):
    async with aiosqlite.connect(_p()) as db:
        # Keep max 5 addresses per user
        async with db.execute(
            "SELECT COUNT(*) FROM saved_addresses WHERE telegram_id=?", (tid,)
        ) as c:
            cnt = (await c.fetchone())[0]
        if cnt >= 5:
            await db.execute(
                """DELETE FROM saved_addresses WHERE id=(
                   SELECT id FROM saved_addresses WHERE telegram_id=? ORDER BY created_at ASC LIMIT 1)""",
                (tid,)
            )
        await db.execute(
            "INSERT INTO saved_addresses(telegram_id, label, address) VALUES(?,?,?)",
            (tid, label, address)
        )
        await db.commit()

async def delete_saved_address(addr_id: int, tid: int):
    async with aiosqlite.connect(_p()) as db:
        await db.execute("DELETE FROM saved_addresses WHERE id=? AND telegram_id=?", (addr_id, tid))
        await db.commit()

# ── PRODUCT STATS (admin) ──
async def get_product_stats() -> list:
    """Top products by quantity sold."""
    async with aiosqlite.connect(_p()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.id, p.name, p.price, p.category,
                   COALESCE(SUM(oi.quantity), 0) as total_sold,
                   COALESCE(SUM(oi.quantity * oi.price), 0) as total_revenue
            FROM products p
            LEFT JOIN order_items oi ON oi.product_id = p.id
            LEFT JOIN orders o ON o.id = oi.order_id AND o.status != 'cancelled'
            WHERE p.is_active = 1
            GROUP BY p.id
            ORDER BY total_sold DESC
        """) as c:
            return await c.fetchall()

# ── DELIVERY ZONES ──
async def get_delivery_zones() -> list:
    """Return configured delivery zones from config (no DB needed)."""
    return []
