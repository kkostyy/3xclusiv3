# handlers/wishlist.py — избранные товары
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database import get_user_language, toggle_wishlist, get_wishlist, is_in_wishlist, get_product
from keyboards import kb_wishlist_item
from locales import gt

log = logging.getLogger(__name__)
router = Router()

_LANGS = ("ru", "en", "et")

WISH_EMPTY = {
    "ru": "🤍 *Избранное пусто*\n\nДобавляйте товары кнопкой 🤍 в карточке товара.",
    "en": "🤍 *Wishlist is empty*\n\nAdd items using the 🤍 button on product cards.",
    "et": "🤍 *Lemmikud on tühi*\n\nLisage tooteid 🤍 nupuga tootelehtedel.",
}
WISH_HEADER = {
    "ru": "❤️ *Избранное ({count} шт.):*\n",
    "en": "❤️ *Wishlist ({count} items):*\n",
    "et": "❤️ *Lemmikud ({count} tk):*\n",
}


@router.message(F.text.func(lambda t: t in [gt("❤️ Избранное", l) for l in _LANGS]))
async def cmd_wishlist(message: Message):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    items = await get_wishlist(tgid)
    if not items:
        await message.answer(WISH_EMPTY.get(lang, WISH_EMPTY["en"]), parse_mode="Markdown")
        return
    await message.answer(WISH_HEADER.get(lang, WISH_HEADER["en"]).format(count=len(items)), parse_mode="Markdown")
    for p in items:
        cap = f"*{p['name']}*\n💰 {p['price']:.2f} €\n\n{p['description'] or ''}"
        try:
            if p["photo_id"]:
                await message.answer_photo(p["photo_id"], caption=cap, parse_mode="Markdown",
                                           reply_markup=kb_wishlist_item(p["id"], lang))
            else:
                await message.answer(cap, parse_mode="Markdown",
                                     reply_markup=kb_wishlist_item(p["id"], lang))
        except Exception as e:
            log.error("Wishlist item send error: %s", e)


@router.callback_query(F.data.startswith("wish:toggle:"))
async def cb_wish_toggle(callback: CallbackQuery):
    pid  = int(callback.data.split(":")[2])
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    p    = await get_product(pid)
    if not p:
        await callback.answer(gt("error", lang), show_alert=True); return

    added = await toggle_wishlist(tgid, pid)
    if added:
        alerts = {"ru": f"❤️ {p['name']} добавлен в избранное", "en": f"❤️ {p['name']} added to wishlist", "et": f"❤️ {p['name']} lisati lemmikutesse"}
    else:
        alerts = {"ru": f"🤍 {p['name']} удалён из избранного", "en": f"🤍 {p['name']} removed from wishlist", "et": f"🤍 {p['name']} eemaldati lemmikutest"}
    await callback.answer(alerts.get(lang, ""), show_alert=True)

    # Update button heart on the card
    from keyboards import kb_product_wish
    try:
        await callback.message.edit_reply_markup(
            reply_markup=kb_product_wish(pid, added, lang)
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("wish:remove:"))
async def cb_wish_remove(callback: CallbackQuery):
    pid  = int(callback.data.split(":")[2])
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    await toggle_wishlist(tgid, pid)  # will remove since it's already there
    removed = {"ru": "🗑 Удалено из избранного", "en": "🗑 Removed from wishlist", "et": "🗑 Eemaldatud lemmikutest"}
    await callback.answer(removed.get(lang, ""), show_alert=False)
    try:
        await callback.message.delete()
    except Exception:
        pass
