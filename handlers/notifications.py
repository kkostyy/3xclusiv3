# handlers/notifications.py — подписки на уведомления о новинках
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

from database import get_user_language, toggle_notification, get_user_notifications, get_subscribers_for_category
from keyboards import kb_notifications
from locales import gt

log = logging.getLogger(__name__)
router = Router()

_LANGS = ("ru", "en", "et")

NOTIF_TITLES = {
    "ru": "🔔 *Уведомления о новинках*\n\nВыберите категории — вы получите сообщение когда появится новый товар:",
    "en": "🔔 *New arrival notifications*\n\nChoose categories — you'll be notified when new items appear:",
    "et": "🔔 *Uute toodete teavitused*\n\nValige kategooriad — saate teate, kui ilmub uus toode:",
}


@router.message(F.text.func(lambda t: t in [gt("🔔 Уведомления", l) for l in _LANGS]))
async def cmd_notifications(message: Message):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    subs = await get_user_notifications(tgid)
    await message.answer(
        NOTIF_TITLES.get(lang, NOTIF_TITLES["en"]),
        reply_markup=kb_notifications(subs, lang),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("notif:toggle:"))
async def cb_notif_toggle(callback: CallbackQuery):
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    cat  = callback.data.split(":")[2]
    subscribed = await toggle_notification(tgid, cat)
    subs = await get_user_notifications(tgid)

    cat_names = {
        "ru": {"clothes": "Одежда", "shoes": "Обувь", "accessories": "Аксессуары"},
        "en": {"clothes": "Clothes", "shoes": "Shoes", "accessories": "Accessories"},
        "et": {"clothes": "Riided", "shoes": "Jalatsid", "accessories": "Aksessuaarid"},
    }.get(lang, {})
    cat_name = cat_names.get(cat, cat)

    if subscribed:
        alerts = {"ru": f"✅ Подписались на *{cat_name}*", "en": f"✅ Subscribed to *{cat_name}*", "et": f"✅ Tellisite *{cat_name}*"}
    else:
        alerts = {"ru": f"🔕 Отписались от *{cat_name}*", "en": f"🔕 Unsubscribed from *{cat_name}*", "et": f"🔕 Loobuste *{cat_name}*"}

    await callback.answer(alerts.get(lang, ""), show_alert=False)
    # Refresh keyboard
    await callback.message.edit_reply_markup(reply_markup=kb_notifications(subs, lang))


async def notify_new_product(bot: Bot, product_name: str, category: str, photo_id: str | None = None):
    """Call this after adding a new product to notify subscribers."""
    subscribers = await get_subscribers_for_category(category)
    cat_labels = {"clothes": "👕", "shoes": "👟", "accessories": "👜"}
    icon = cat_labels.get(category, "🛍")
    for tid in subscribers:
        lang = await get_user_language(tid)
        texts = {
            "ru": f"🔔 *Новинка!* {icon}\n\n*{product_name}* теперь доступен в каталоге!",
            "en": f"🔔 *New arrival!* {icon}\n\n*{product_name}* is now available in the catalog!",
            "et": f"🔔 *Uus toode!* {icon}\n\n*{product_name}* on nüüd kataloogis saadaval!",
        }
        try:
            if photo_id:
                await bot.send_photo(tid, photo_id, caption=texts.get(lang, texts["en"]), parse_mode="Markdown")
            else:
                await bot.send_message(tid, texts.get(lang, texts["en"]), parse_mode="Markdown")
        except Exception as e:
            log.warning("Cannot notify user %s: %s", tid, e)
