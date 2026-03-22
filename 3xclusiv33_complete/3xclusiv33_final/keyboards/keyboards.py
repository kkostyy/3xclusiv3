# keyboards/keyboards.py

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from locales import gt

# ── Выбор языка (inline — используется только при первом запуске и в настройках) ──
def kb_lang() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🇷🇺 Русский", callback_data="lang:ru")
    b.button(text="🇬🇧 English", callback_data="lang:en")
    b.button(text="🇪🇪 Eesti",   callback_data="lang:et")
    b.adjust(1)
    return b.as_markup()

# ── Меню пользователя — только главное ───────────────────────────────────────
def kb_user(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    # Ряд 1 — главные действия
    b.button(text=gt("🛍 Каталог",    lang))
    b.button(text=gt("🛒 Корзина",    lang))
    # Ряд 2
    b.button(text=gt("📦 Мои заказы", lang))
    b.button(text=gt("❤️ Избранное",  lang))
    # Ряд 3
    b.button(text=gt("💬 Продавец",   lang))
    b.button(text=gt("☰ Ещё",         lang))
    b.adjust(2, 2, 2)
    return b.as_markup(resize_keyboard=True, input_field_placeholder="Выберите раздел...")

# ── Подменю "Ещё" для пользователя ───────────────────────────────────────────
def kb_user_more(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=gt("🔔 Уведомления", lang))
    b.button(text=gt("📍 Адреса",      lang))
    b.button(text=gt("🔗 Рефералы",    lang))
    b.button(text=gt("📏 Размер",      lang))
    b.button(text=gt("🚚 Доставка",    lang))
    b.button(text=gt("⚙️ Настройки",  lang))
    b.button(text=gt("🔙 Назад",       lang))
    b.adjust(2, 2, 2, 1)
    return b.as_markup(resize_keyboard=True, input_field_placeholder="...")

# ── Меню админа — только главное ─────────────────────────────────────────────
def kb_admin(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=gt("📦 Товары",    lang))
    b.button(text=gt("📋 Заказы",   lang))
    b.button(text=gt("📸 QC",       lang))
    b.button(text=gt("📊 Статистика", lang))
    b.button(text=gt("💬 Продавец", lang))
    b.button(text=gt("☰ Ещё",       lang))
    b.adjust(2, 2, 2)
    return b.as_markup(resize_keyboard=True, input_field_placeholder="Панель администратора")

# ── Подменю "Ещё" для админа ──────────────────────────────────────────────────
def kb_admin_more(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=gt("⭐ Отзывы",       lang))
    b.button(text=gt("📈 Товары стат",  lang))
    b.button(text=gt("🔗 Рефералы адм", lang))
    b.button(text=gt("📣 Рассылка",     lang))
    b.button(text=gt("🚚 Доставка",     lang))
    b.button(text=gt("⚙️ Настройки",   lang))
    b.button(text=gt("🔙 Назад",        lang))
    b.adjust(2, 2, 2, 1)
    return b.as_markup(resize_keyboard=True, input_field_placeholder="...")

def kb_menu(lang: str, is_adm: bool) -> ReplyKeyboardMarkup:
    return kb_admin(lang) if is_adm else kb_user(lang)

def kb_more(lang: str, is_adm: bool) -> ReplyKeyboardMarkup:
    return kb_admin_more(lang) if is_adm else kb_user_more(lang)

# ── Настройки (inline) ────────────────────────────────────────────────────────
def kb_settings(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=gt("👤 Профиль", lang), callback_data="settings:profile")
    b.button(text=gt("🌍 Язык",    lang), callback_data="settings:lang")
    b.adjust(2)
    return b.as_markup()

# ── Отмена ────────────────────────────────────────────────────────────────────
def kb_cancel(lang: str) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.button(text=gt("❌ Отмена", lang))
    return b.as_markup(resize_keyboard=True, one_time_keyboard=True)

# ── Категории ─────────────────────────────────────────────────────────────────
def kb_categories(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=gt("👕 Одежда",     lang), callback_data="cat:clothes")
    b.button(text=gt("👟 Обувь",      lang), callback_data="cat:shoes")
    b.button(text=gt("👜 Аксессуары", lang), callback_data="cat:accessories")
    b.adjust(1)
    return b.as_markup()

# ── Карточка товара ───────────────────────────────────────────────────────────
def kb_product(pid: int, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=gt("🛒 В корзину", lang), callback_data=f"addcart:{pid}")
    b.button(text=gt("⬅️ Назад",     lang), callback_data="cat:back")
    b.adjust(1)
    return b.as_markup()

# ── Карточка товара с избранным ───────────────────────────────────────────────
def kb_product_wish(pid: int, in_wish: bool, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    heart = "❤️ " if in_wish else "🤍 "
    wish_labels = {"ru": "Избранное", "en": "Wishlist", "et": "Lemmikud"}
    b.button(text=gt("🛒 В корзину", lang), callback_data=f"addcart:{pid}")
    b.button(text=f"{heart}{wish_labels.get(lang, 'Wishlist')}", callback_data=f"wish:toggle:{pid}")
    b.button(text=gt("⬅️ Назад",     lang), callback_data="cat:back")
    b.adjust(2, 1)
    return b.as_markup()

# ── Корзина ───────────────────────────────────────────────────────────────────
def kb_cart(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=gt("✅ Оформить",  lang), callback_data="cart:checkout")
    b.button(text=gt("🗑 Очистить", lang), callback_data="cart:clear")
    b.adjust(1)
    return b.as_markup()

# ── Подтверждение заказа ──────────────────────────────────────────────────────
def kb_confirm(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=gt("✅ Подтвердить", lang), callback_data="order:confirm")
    b.button(text=gt("✏️ Изменить",   lang), callback_data="order:reenter")
    b.adjust(2)
    return b.as_markup()

# ── Статусы (для админа) ──────────────────────────────────────────────────────
STATUSES = ["searching", "ordered", "in_transit", "arrived", "delivered"]

def status_text(status: str, lang: str) -> str:
    return gt(status, lang)

def kb_statuses(order_id: int, lang: str, buyer_tgid: int = 0) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in STATUSES:
        b.button(text=gt(s, lang), callback_data=f"setstatus:{order_id}:{s}")
    adj_labels   = {"ru": "💲 Скорректировать цену", "en": "💲 Adjust price",    "et": "💲 Korrigeeri hinda"}
    write_labels = {"ru": "✉️ Написать покупателю",  "en": "✉️ Write to buyer",  "et": "✉️ Kirjuta ostjale"}
    b.button(text=adj_labels.get(lang,   "💲 Adjust price"),    callback_data=f"adjprice:{order_id}")
    b.button(text=write_labels.get(lang, "✉️ Write to buyer"),  callback_data=f"writebuyer:{order_id}:{buyer_tgid}")
    b.adjust(2, 2, 1, 2)
    return b.as_markup()

def kb_orders_list(orders: list, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for o in orders:
        b.button(
            text=f"#{o['id']} {gt(o['status'], lang)} — {o['total_price']:.0f}€",
            callback_data=f"adminorder:{o['id']}"
        )
    b.adjust(1)
    return b.as_markup()

# ── QC ────────────────────────────────────────────────────────────────────────
def kb_qc(qc_id: int, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=gt("✅ Принять",   lang), callback_data=f"qc:accept:{qc_id}")
    b.button(text=gt("❌ Отклонить", lang), callback_data=f"qc:reject:{qc_id}")
    b.adjust(2)
    return b.as_markup()

# ── Оценка заказа ─────────────────────────────────────────────────────────────
def kb_rating(order_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for i in range(1, 6):
        b.button(text="⭐" * i, callback_data=f"rate:{order_id}:{i}")
    b.adjust(5)
    return b.as_markup()

# ── Кнопка отмены заказа ──────────────────────────────────────────────────────
def kb_cancel_order(order_id: int, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=gt("❌ Отменить заказ", lang), callback_data=f"cancelorder:{order_id}")
    return b.as_markup()

# ── Корректировка цены — решение покупателя ───────────────────────────────────
def kb_price_decision(oid: int, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    accept = {"ru": "✅ Принять новую цену", "en": "✅ Accept new price", "et": "✅ Nõustun uue hinnaga"}
    reject = {"ru": "❌ Отменить заказ",     "en": "❌ Cancel order",     "et": "❌ Tühistan tellimuse"}
    b.button(text=accept.get(lang, "✅ Accept"), callback_data=f"priceok:{oid}")
    b.button(text=reject.get(lang, "❌ Cancel"), callback_data=f"pricecancel:{oid}")
    b.adjust(1)
    return b.as_markup()

# ── Товары (админ) ────────────────────────────────────────────────────────────
def kb_admin_products(lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=gt("➕ Добавить",       lang), callback_data="aprod:add")
    b.button(text=gt("✏️ Редактировать", lang), callback_data="aprod:edit")
    b.button(text=gt("🗑 Удалить",        lang), callback_data="aprod:delete")
    stock_labels = {"ru": "📦 Наличие", "en": "📦 Stock", "et": "📦 Laoseis"}
    b.button(text=stock_labels.get(lang, "📦 Stock"), callback_data="aprod:stock")
    b.adjust(1)
    return b.as_markup()

def kb_product_list(products: list, action: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        icon = "✏️" if action == "edit" else "🗑"
        b.button(text=f"{icon} {p['name']} — {p['price']}€",
                 callback_data=f"aprod:{action}:{p['id']}")
    b.adjust(1)
    return b.as_markup()

def kb_stock_list(products: list, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        avail = p["is_available"] if "is_available" in p.keys() else 1
        icon  = "✅" if avail else "🚫"
        b.button(
            text=f"{icon} {p['name']} — {p['price']}€",
            callback_data=f"aprod:togglestock:{p['id']}"
        )
    b.adjust(1)
    return b.as_markup()

def kb_cat_admin() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="👕 Одежда",     callback_data="prodcat:clothes")
    b.button(text="👟 Обувь",      callback_data="prodcat:shoes")
    b.button(text="👜 Аксессуары", callback_data="prodcat:accessories")
    b.adjust(1)
    return b.as_markup()

# ── Уведомления ───────────────────────────────────────────────────────────────
def kb_notifications(subscribed: list, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    cats = [("clothes", "👕"), ("shoes", "👟"), ("accessories", "👜")]
    labels = {
        "ru": {"clothes": "Одежда", "shoes": "Обувь", "accessories": "Аксессуары"},
        "en": {"clothes": "Clothes", "shoes": "Shoes", "accessories": "Accessories"},
        "et": {"clothes": "Riided", "shoes": "Jalatsid", "accessories": "Aksessuaarid"},
    }.get(lang, {})
    for cat, emoji in cats:
        check = "✅" if cat in subscribed else "☐"
        b.button(text=f"{check} {emoji} {labels.get(cat, cat)}", callback_data=f"notif:toggle:{cat}")
    b.adjust(1)
    return b.as_markup()

# ── Избранное ─────────────────────────────────────────────────────────────────
def kb_wishlist_item(pid: int, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    cart_labels = {"ru": "🛒 В корзину", "en": "🛒 Add to cart", "et": "🛒 Lisa korvi"}
    rm_labels   = {"ru": "🗑 Удалить",   "en": "🗑 Remove",       "et": "🗑 Eemalda"}
    b.button(text=cart_labels.get(lang, "🛒 Add to cart"), callback_data=f"addcart:{pid}")
    b.button(text=rm_labels.get(lang,   "🗑 Remove"),      callback_data=f"wish:remove:{pid}")
    b.adjust(2)
    return b.as_markup()

# ── Сохранённые адреса ────────────────────────────────────────────────────────
def kb_saved_addresses(addresses: list, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for a in addresses:
        b.button(text=f"📍 {a['label']}", callback_data=f"addr:use:{a['id']}")
    new_labels = {"ru": "✏️ Ввести новый", "en": "✏️ Enter new", "et": "✏️ Sisesta uus"}
    b.button(text=new_labels.get(lang, "✏️ Enter new"), callback_data="addr:new")
    b.adjust(1)
    return b.as_markup()

def kb_address_manage(addresses: list, lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for a in addresses:
        b.button(text=f"🗑 {a['label']}", callback_data=f"addr:del:{a['id']}")
    b.adjust(1)
    return b.as_markup()
