# handlers/admin_misc.py — статистика, рассылка, отзывы, рефералы
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user_language, get_all_reviews, get_all_referrals, get_all_orders, get_all_products, get_product_stats
from keyboards import kb_cancel, kb_menu
from locales import gt
from utils import is_admin
import aiosqlite
from config import DATABASE_PATH

log = logging.getLogger(__name__)
router = Router()

def _is_cancel(t): return t in [gt("❌ Отмена", l) for l in ("ru","en","et")]


class Broadcast(StatesGroup):
    waiting = State()


@router.message(F.text.func(lambda t: t in [gt("📊 Статистика", l) for l in ("ru","en","et")]))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id): return
    orders    = await get_all_orders()
    products  = await get_all_products()
    reviews   = await get_all_reviews()
    referrals = await get_all_referrals()
    revenue   = sum(o["total_price"] for o in orders if o["status"] != "cancelled")
    delivered = sum(1 for o in orders if o["status"] == "delivered")
    cancelled = sum(1 for o in orders if o["status"] == "cancelled")
    active    = len(orders) - delivered - cancelled
    avg       = (sum(r["rating"] for r in reviews) / len(reviews)) if reviews else 0.0

    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            row = await c.fetchone()
            users = row[0] if row else 0

    await message.answer(
        "📊 *СТАТИСТИКА МАГАЗИНА*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Пользователей: *{users}*\n"
        f"🔗 Рефералов: *{len(referrals)}*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Заказов всего: *{len(orders)}*\n"
        f"  ✅ Выполнено: *{delivered}*\n"
        f"  🔄 Активных: *{active}*\n"
        f"  ❌ Отменено: *{cancelled}*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Выручка: *{revenue:.2f} €*\n"
        f"🛍 Товаров: *{len(products)}*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ Отзывов: *{len(reviews)}*\n"
        f"⭐ Средняя оценка: *{avg:.1f}/5*",
        parse_mode="Markdown"
    )


@router.message(F.text.func(lambda t: t in [gt("📣 Рассылка", l) for l in ("ru","en","et")]))
async def cmd_broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    lang = await get_user_language(message.from_user.id)
    await state.set_state(Broadcast.waiting)
    await message.answer(
        "📣 *Рассылка*\n\nНапишите сообщение для всех пользователей.\nПоддерживается текст и фото.",
        reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(Broadcast.waiting)
async def cmd_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    if _is_cancel(message.text or ""):
        await state.clear(); await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True)); return

    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT telegram_id FROM users") as c:
            rows = await c.fetchall()

    sent = 0; failed = 0
    for row in rows:
        uid = row[0]
        if uid == tgid: continue
        try:
            if message.photo:
                await bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption or "", parse_mode="Markdown")
            else:
                await bot.send_message(uid, message.text, parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1

    await state.clear()
    await message.answer(f"📣 *Рассылка завершена!*\n\n✅ Доставлено: *{sent}*\n❌ Ошибок: *{failed}*",
                         reply_markup=kb_menu(lang, True), parse_mode="Markdown")


@router.message(F.text.func(lambda t: t in [gt("⭐ Отзывы", l) for l in ("ru","en","et")]))
async def cmd_reviews(message: Message):
    if not is_admin(message.from_user.id): return
    lang    = await get_user_language(message.from_user.id)
    reviews = await get_all_reviews()
    if not reviews:
        await message.answer(gt("no_reviews", lang)); return
    text = f"⭐ *Отзывы ({len(reviews)}):*\n\n"
    for r in reviews:
        text += f"{'⭐'*r['rating']} | 👤 `{r['telegram_id']}` | 📦 #{r['order_id']}\n💬 {r['comment'] or '—'}\n📅 {str(r['created_at'])[:10]}\n\n"
        if len(text) > 3500:
            await message.answer(text, parse_mode="Markdown"); text = ""
    if text.strip(): await message.answer(text, parse_mode="Markdown")


@router.message(F.text.func(lambda t: t in [gt("🔗 Рефералы адм", l) for l in ("ru","en","et")]))
async def cmd_referrals(message: Message):
    if not is_admin(message.from_user.id): return
    lang = await get_user_language(message.from_user.id)
    refs = await get_all_referrals()
    if not refs:
        await message.answer(gt("no_referrals", lang)); return
    text = f"🔗 *Рефералы ({len(refs)}):*\n\n"
    for r in refs:
        text += f"{'✅' if r['bonus_paid'] else '⏳'} `{r['user_id']}` → `{r['invited_user_id']}` | {str(r['created_at'])[:10]}\n"
        if len(text) > 3500:
            await message.answer(text, parse_mode="Markdown"); text = ""
    if text.strip(): await message.answer(text, parse_mode="Markdown")


# ── Статистика по товарам ──────────────────────────────────────────────────────
@router.message(F.text.func(lambda t: t in [gt("📈 Товары стат", l) for l in ("ru","en","et")]))
async def cmd_product_stats(message: Message):
    if not is_admin(message.from_user.id): return
    stats = await get_product_stats()
    if not stats:
        await message.answer("❌ Нет данных."); return

    cat_icons = {"clothes": "👕", "shoes": "👟", "accessories": "👜"}
    text = "📈 *Статистика по товарам*\n━━━━━━━━━━━━━━━━━━━\n"
    for i, p in enumerate(stats[:10], 1):
        icon = cat_icons.get(p["category"], "🛍")
        revenue_str = f"{p['total_revenue']:.2f} €" if p["total_sold"] > 0 else "—"
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        text += (
            f"{medal} {icon} *{p['name']}*\n"
            f"   💰 {p['price']} € | 📦 Продано: *{p['total_sold']} шт.* | 💵 {revenue_str}\n"
        )
    text += "━━━━━━━━━━━━━━━━━━━"
    await message.answer(text, parse_mode="Markdown")


# ── Зоны доставки ──────────────────────────────────────────────────────────────
DELIVERY_ZONES = {
    "ru": [
        ("🏙 Таллин — Центр",       "Kesklinn, Põhja-Tallinn, Kalamaja", "0 €",   "В день заказа"),
        ("🏘 Таллин — Периферия",   "Lasnamäe, Mustamäe, Kristiine, Haabersti, Pirita", "0 €", "В день заказа"),
        ("🚌 Харьюмаа",             "Маарду, Саку, Кейла, Виймси", "2 €",   "1–2 дня"),
        ("🚗 Другие регионы",       "Тарту, Пярну, Нарва и другие", "5 €",   "2–3 дня"),
    ],
    "en": [
        ("🏙 Tallinn — Centre",     "Kesklinn, Põhja-Tallinn, Kalamaja", "0 €",   "Same day"),
        ("🏘 Tallinn — Suburbs",    "Lasnamäe, Mustamäe, Kristiine, Haabersti, Pirita", "0 €", "Same day"),
        ("🚌 Harjumaa",             "Maardu, Saue, Keila, Viimsi", "2 €",   "1–2 days"),
        ("🚗 Other regions",        "Tartu, Pärnu, Narva and others", "5 €",   "2–3 days"),
    ],
    "et": [
        ("🏙 Tallinn — Kesklinn",   "Kesklinn, Põhja-Tallinn, Kalamaja", "0 €",   "Samal päeval"),
        ("🏘 Tallinn — Äärelinnad", "Lasnamäe, Mustamäe, Kristiine, Haabersti, Pirita", "0 €", "Samal päeval"),
        ("🚌 Harjumaa",             "Maardu, Saue, Keila, Viimsi", "2 €",   "1–2 päeva"),
        ("🚗 Muud piirkonnad",      "Tartu, Pärnu, Narva jt", "5 €",   "2–3 päeva"),
    ],
}

@router.message(F.text.func(lambda t: t in [gt("🚚 Доставка", l) for l in ("ru","en","et")]))
async def cmd_delivery_zones(message: Message):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    zones = DELIVERY_ZONES.get(lang, DELIVERY_ZONES["en"])
    headers = {
        "ru": "🚚 *Зоны доставки*\n━━━━━━━━━━━━━━━━━━━",
        "en": "🚚 *Delivery zones*\n━━━━━━━━━━━━━━━━━━━",
        "et": "🚚 *Tarnepiirkonnad*\n━━━━━━━━━━━━━━━━━━━",
    }
    cost_label = {"ru": "Стоимость", "en": "Cost", "et": "Hind"}
    time_label = {"ru": "Срок",      "en": "Time", "et": "Aeg"}
    text = headers.get(lang, headers["en"]) + "\n\n"
    for name, areas, cost, timing in zones:
        text += (
            f"*{name}*\n"
            f"📌 _{areas}_\n"
            f"💰 {cost_label.get(lang,'Cost')}: *{cost}* | ⏱ {time_label.get(lang,'Time')}: *{timing}*\n\n"
        )
    note = {
        "ru": "_Оплата наличными при встрече с продавцом_",
        "en": "_Cash payment upon meeting the seller_",
        "et": "_Tasumine sularahas müüjaga kohtumisel_",
    }
    text += "━━━━━━━━━━━━━━━━━━━\n" + note.get(lang, note["en"])
    await message.answer(text, parse_mode="Markdown")
