# handlers/admin_products.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_user_language, get_all_products, get_product, add_product, update_product, delete_product, toggle_product_availability
from keyboards import kb_admin_products, kb_product_list, kb_cat_admin, kb_gender_admin, kb_menu, kb_cancel, kb_stock_list
from locales import gt
from states import AdminAddProduct, AdminEditProduct
from utils import is_admin

log = logging.getLogger(__name__)
router = Router()

def _is_cancel(t): return t in [gt("❌ Отмена", l) for l in ("ru","en","et")]


@router.message(F.text.func(lambda t: t in [gt("📦 Товары", l) for l in ("ru","en","et")]))
async def cmd_admin_products(message: Message):
    if not is_admin(message.from_user.id): return
    lang = await get_user_language(message.from_user.id)
    await message.answer(gt("admin_products_menu", lang), reply_markup=kb_admin_products(lang), parse_mode="Markdown")


@router.callback_query(F.data == "aprod:add")
async def cb_add(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    lang = await get_user_language(callback.from_user.id)
    await state.set_state(AdminAddProduct.waiting_name)
    await callback.message.answer(gt("enter_prod_name", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")
    await callback.answer()


@router.message(AdminAddProduct.waiting_name)
async def ap_name(message: Message, state: FSMContext):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear(); await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True)); return
    await state.update_data(p_name=message.text)
    await state.set_state(AdminAddProduct.waiting_price)
    await message.answer(gt("enter_prod_price", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(AdminAddProduct.waiting_price)
async def ap_price(message: Message, state: FSMContext):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear(); await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True)); return
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(gt("invalid_number", lang)); return
    await state.update_data(p_price=price)
    await state.set_state(AdminAddProduct.waiting_category)
    await message.answer(gt("choose_cat_admin", lang), reply_markup=kb_cat_admin(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("prodcat:"))
async def ap_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    cat  = callback.data.split(":")[1]
    lang = await get_user_language(callback.from_user.id)
    await state.update_data(p_cat=cat)
    await state.set_state(AdminAddProduct.waiting_gender)
    gender_labels = {"ru": "Выберите пол товара:", "en": "Select gender:", "et": "Vali sugu:"}
    await callback.message.answer(gender_labels.get(lang, "Выберите пол:"), reply_markup=kb_gender_admin())
    await callback.answer()

@router.callback_query(F.data.startswith("prodgender:"))
async def ap_gender(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    gender = callback.data.split(":")[1]
    lang   = await get_user_language(callback.from_user.id)
    await state.update_data(p_gender=gender)
    await state.set_state(AdminAddProduct.waiting_desc)
    await callback.message.answer(gt("enter_prod_desc", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")
    await callback.answer()


@router.message(AdminAddProduct.waiting_desc)
async def ap_desc(message: Message, state: FSMContext):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear(); await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True)); return
    await state.update_data(p_desc=message.text)
    await state.set_state(AdminAddProduct.waiting_photo)
    await message.answer(gt("send_prod_photo", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(AdminAddProduct.waiting_photo, F.photo)
async def ap_photo(message: Message, state: FSMContext):
    tgid  = message.from_user.id; lang = await get_user_language(tgid)
    photo = message.photo[-1].file_id; data = await state.get_data()
    pid   = await add_product(data["p_name"], data["p_price"], data["p_cat"], data["p_desc"], photo, gender=data.get("p_gender", "unisex"))
    await state.clear()
    await message.answer(f"{gt('product_added', lang)} (ID #{pid})", reply_markup=kb_menu(lang, True))
    log.info("Admin added product #%s", pid)
    # Notify subscribers about new product
    from handlers.notifications import notify_new_product
    await notify_new_product(message.bot, data["p_name"], data["p_cat"], photo)


@router.callback_query(F.data == "aprod:edit")
async def cb_edit_list(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    lang     = await get_user_language(callback.from_user.id)
    products = await get_all_products()
    if not products:
        await callback.answer(gt("no_products_admin", lang), show_alert=True); return
    await state.set_state(AdminEditProduct.select_product)
    await callback.message.edit_text(gt("select_product", lang), reply_markup=kb_product_list(products, "edit"))
    await callback.answer()


@router.callback_query(F.data.startswith("aprod:edit:"))
async def cb_edit_select(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    pid  = int(callback.data.split(":")[2]); lang = await get_user_language(callback.from_user.id)
    p    = await get_product(pid)
    if not p: await callback.answer(gt("error", lang), show_alert=True); return
    await state.update_data(edit_pid=pid)
    await state.set_state(AdminEditProduct.waiting_name)
    await callback.message.answer(
        f"*Текущее название:* {p['name']}\n\n{gt('enter_prod_name', lang)}",
        reply_markup=kb_cancel(lang), parse_mode="Markdown")
    await callback.answer()


@router.message(AdminEditProduct.waiting_name)
async def ep_name(message: Message, state: FSMContext):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear(); await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True)); return
    await state.update_data(p_name=message.text)
    await state.set_state(AdminEditProduct.waiting_price)
    await message.answer(gt("enter_prod_price", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(AdminEditProduct.waiting_price)
async def ep_price(message: Message, state: FSMContext):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear(); await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True)); return
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(gt("invalid_number", lang)); return
    await state.update_data(p_price=price)
    await state.set_state(AdminEditProduct.waiting_desc)
    await message.answer(gt("enter_prod_desc", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(AdminEditProduct.waiting_desc)
async def ep_desc(message: Message, state: FSMContext):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear(); await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True)); return
    await state.update_data(p_desc=message.text)
    await state.set_state(AdminEditProduct.waiting_photo)
    await message.answer(gt("send_prod_photo", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(AdminEditProduct.waiting_photo, F.photo)
async def ep_photo(message: Message, state: FSMContext):
    tgid  = message.from_user.id; lang = await get_user_language(tgid)
    photo = message.photo[-1].file_id; data = await state.get_data()
    await update_product(data["edit_pid"], data["p_name"], data["p_price"], data["p_desc"], photo)
    await state.clear()
    await message.answer(gt("product_updated", lang), reply_markup=kb_menu(lang, True))


@router.callback_query(F.data == "aprod:delete")
async def cb_delete_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    lang     = await get_user_language(callback.from_user.id)
    products = await get_all_products()
    if not products:
        await callback.answer(gt("no_products_admin", lang), show_alert=True); return
    await callback.message.edit_text(gt("select_product", lang), reply_markup=kb_product_list(products, "delete"))
    await callback.answer()


@router.callback_query(F.data.startswith("aprod:delete:"))
async def cb_delete_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    pid  = int(callback.data.split(":")[2]); lang = await get_user_language(callback.from_user.id)
    await delete_product(pid)
    await callback.message.edit_text(gt("product_deleted", lang))
    await callback.answer()


# ── Стоп-лист / Наличие ───────────────────────────────────────────────────────
@router.callback_query(F.data == "aprod:stock")
async def cb_stock_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    lang     = await get_user_language(callback.from_user.id)
    products = await get_all_products()
    if not products:
        await callback.answer(gt("no_products_admin", lang), show_alert=True); return

    headers = {
        "ru": "📦 *Управление наличием*\n✅ — в наличии  |  🚫 — нет в наличии\n\nНажмите на товар чтобы переключить:",
        "en": "📦 *Stock management*\n✅ — in stock  |  🚫 — out of stock\n\nTap item to toggle:",
        "et": "📦 *Laoseisu haldus*\n✅ — laos  |  🚫 — otsas\n\nVajutage üksusele ümberlülitamiseks:",
    }
    await callback.message.edit_text(headers.get(lang, headers["en"]),
                                      reply_markup=kb_stock_list(products, lang),
                                      parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("aprod:togglestock:"))
async def cb_toggle_stock(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    pid      = int(callback.data.split(":")[2])
    lang     = await get_user_language(callback.from_user.id)
    p        = await get_product(pid)
    if not p:
        await callback.answer(gt("error", lang), show_alert=True); return

    new_state = await toggle_product_availability(pid)

    # Alert to admin
    if new_state:
        alert = {"ru": f"✅ «{p['name']}» — в наличии",
                 "en": f"✅ «{p['name']}» — in stock",
                 "et": f"✅ «{p['name']}» — laos"}
    else:
        alert = {"ru": f"🚫 «{p['name']}» — нет в наличии",
                 "en": f"🚫 «{p['name']}» — out of stock",
                 "et": f"🚫 «{p['name']}» — otsas"}
    await callback.answer(alert.get(lang, ""), show_alert=True)

    # Refresh the stock list
    products = await get_all_products()
    headers  = {
        "ru": "📦 *Управление наличием*\n✅ — в наличии  |  🚫 — нет в наличии\n\nНажмите на товар чтобы переключить:",
        "en": "📦 *Stock management*\n✅ — in stock  |  🚫 — out of stock\n\nTap item to toggle:",
        "et": "📦 *Laoseisu haldus*\n✅ — laos  |  🚫 — otsas\n\nVajutage üksusele ümberlülitamiseks:",
    }
    try:
        await callback.message.edit_text(headers.get(lang, headers["en"]),
                                          reply_markup=kb_stock_list(products, lang),
                                          parse_mode="Markdown")
    except Exception:
        pass

    # If marked out of stock — notify wishlist users
    if not new_state:
        from database import get_available_products
        import aiosqlite
        from config import DATABASE_PATH
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT telegram_id FROM wishlist WHERE product_id=?", (pid,)
            ) as c:
                wish_users = [r["telegram_id"] for r in await c.fetchall()]
        for uid in wish_users:
            ul = await get_user_language(uid)
            notif = {
                "ru": f"😔 Товар *{p['name']}* временно закончился.",
                "en": f"😔 *{p['name']}* is temporarily out of stock.",
                "et": f"😔 *{p['name']}* on ajutiselt otsas.",
            }
            try:
                await callback.bot.send_message(uid, notif.get(ul, notif["en"]), parse_mode="Markdown")
            except Exception:
                pass
