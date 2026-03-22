# handlers/catalog.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import get_products_by_category, get_product, get_user_language, is_in_wishlist
from keyboards import kb_categories, kb_product, kb_product_wish
from locales import gt
from utils import add_to_cart

log = logging.getLogger(__name__)
router = Router()

_cat_map = {"clothes": "👕 Одежда", "shoes": "👟 Обувь", "accessories": "👜 Аксессуары"}
_product_msgs: dict[int, list] = {}


async def _del_products(bot, chat_id, uid):
    for mid in _product_msgs.get(uid, []):
        try: await bot.delete_message(chat_id, mid)
        except: pass
    _product_msgs[uid] = []


@router.message(F.text.func(lambda t: t in [gt("🛍 Каталог", l) for l in ("ru","en","et")]))
async def cmd_catalog(message: Message):
    lang = await get_user_language(message.from_user.id)
    await _del_products(message.bot, message.chat.id, message.from_user.id)
    await message.answer(gt("choose_category", lang), reply_markup=kb_categories(lang))


@router.callback_query(F.data.startswith("cat:") & ~F.data.eq("cat:back"))
async def cb_category(callback: CallbackQuery):
    cat  = callback.data.split(":")[1]
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    await _del_products(callback.bot, callback.message.chat.id, tgid)

    products = await get_products_by_category(cat)
    if not products:
        await callback.answer(gt("no_products", lang), show_alert=True)
        return

    cat_name = gt(_cat_map.get(cat, "🛍 Каталог"), lang)
    b = InlineKeyboardBuilder()
    b.button(text=gt("⬅️ Назад", lang), callback_data="cat:back")
    count_label = {"ru": "шт.", "en": "items", "et": "tk."}.get(lang, "шт.")
    try:
        await callback.message.edit_text(f"{cat_name} — {len(products)} {count_label}", reply_markup=b.as_markup())
    except TelegramBadRequest:
        pass

    sent = []
    for p in products:
        cap = f"*{p['name']}*\n💰 {p['price']:.2f} €\n\n{p['description'] or ''}"
        in_wish = await is_in_wishlist(tgid, p["id"])
        kb = kb_product_wish(p["id"], in_wish, lang)
        try:
            if p["photo_id"]:
                msg = await callback.message.answer_photo(p["photo_id"], caption=cap, parse_mode="Markdown", reply_markup=kb)
            else:
                msg = await callback.message.answer(cap, parse_mode="Markdown", reply_markup=kb)
            sent.append(msg.message_id)
        except Exception as e:
            log.error("Product send error: %s", e)
    _product_msgs[tgid] = sent
    await callback.answer()


@router.callback_query(F.data == "cat:back")
async def cb_back(callback: CallbackQuery):
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    await _del_products(callback.bot, callback.message.chat.id, tgid)
    try:
        await callback.message.edit_text(gt("choose_category", lang), reply_markup=kb_categories(lang))
    except TelegramBadRequest:
        await callback.message.answer(gt("choose_category", lang), reply_markup=kb_categories(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("addcart:"))
async def cb_add_cart(callback: CallbackQuery):
    pid  = int(callback.data.split(":")[1])
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    p    = await get_product(pid)
    if not p:
        await callback.answer(gt("error", lang), show_alert=True); return
    add_to_cart(tgid, pid, p["name"], p["price"], p["photo_id"])
    await callback.answer(gt("added_to_cart", lang, name=p["name"]), show_alert=True)
