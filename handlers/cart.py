# handlers/cart.py
import logging
import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import (get_user_language, create_order, add_order_item,
                      get_unpaid_referral, mark_referral_bonus_paid,
                      update_user_balance, count_referrals,
                      get_saved_addresses, save_address)
from keyboards import kb_cart, kb_cancel, kb_confirm, kb_menu, kb_saved_addresses
from locales import gt
from states import Checkout
from utils import format_cart, cart_empty, clear_cart, cart_total, cart_items, is_admin, build_receipt, get_referral_discount, apply_discount
from config import ADMIN_IDS, REFERRAL_TIERS

log = logging.getLogger(__name__)
router = Router()

def _is_cancel(t): return t in [gt("❌ Отмена", l) for l in ("ru","en","et")]


@router.message(F.text.func(lambda t: t in [gt("🛒 Корзина", l) for l in ("ru","en","et")]))
async def cmd_cart(message: Message):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    if cart_empty(tgid):
        await message.answer(gt("cart_empty", lang)); return

    items = cart_items(tgid)
    total = cart_total(tgid)

    # Показываем каждый товар с фото
    for item in items:
        photo = item.get("photo_id")
        cap = (
            f"*{item['name']}*\n"
            f"💰 {item['price']:.2f} € × {item['qty']} шт. = *{item['price']*item['qty']:.2f} €*"
        )
        try:
            if photo:
                await message.answer_photo(photo, caption=cap, parse_mode="Markdown")
            else:
                await message.answer(cap, parse_mode="Markdown")
        except Exception as e:
            log.error("Cart photo error: %s", e)
            await message.answer(cap, parse_mode="Markdown")

    # Итого с кнопками
    header = {"ru": "🛒 *Итого:*", "en": "🛒 *Total:*", "et": "🛒 *Kokku:*"}.get(lang, "🛒 *Total:*")
    await message.answer(
        f"{header} *{total:.2f} €*",
        reply_markup=kb_cart(lang),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "cart:clear")
async def cb_clear(callback: CallbackQuery):
    lang = await get_user_language(callback.from_user.id)
    clear_cart(callback.from_user.id)
    await callback.message.edit_text(gt("cart_cleared", lang))
    await callback.answer()


@router.callback_query(F.data == "cart:checkout")
async def cb_checkout(callback: CallbackQuery, state: FSMContext):
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    if cart_empty(tgid):
        await callback.answer(gt("cart_empty", lang), show_alert=True); return
    # Сохраняем скидку в state сразу при начале оформления
    cnt  = await count_referrals(tgid)
    disc = get_referral_discount(cnt)
    await state.update_data(discount_pct=disc)
    await state.set_state(Checkout.waiting_name)
    await callback.message.answer(gt("enter_name", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")
    await callback.answer()


# ── Шаг 1: Имя и Фамилия ─────────────────────────────────────────────────────
@router.message(Checkout.waiting_name)
async def co_name(message: Message, state: FSMContext):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear()
        await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, is_admin(tgid)))
        return
    name = message.text.strip()
    # Имя + Фамилия: минимум 2 слова, только буквы (лат/кир/эст), пробелы и дефисы
    words = name.split()
    if len(words) < 2 or not re.fullmatch(
        r"[A-Za-zÀ-ÖØ-öø-ÿА-яЁёÄäÖöÜüŠšŽž'\- ]{2,60}", name
    ):
        await message.answer(gt("invalid_name", lang), parse_mode="Markdown")
        return
    await state.update_data(cname=name)
    await state.set_state(Checkout.waiting_username)
    await message.answer(gt("enter_username", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


# ── Шаг 2: Telegram username ──────────────────────────────────────────────────
@router.message(Checkout.waiting_username)
async def co_username(message: Message, state: FSMContext):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear()
        await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, is_admin(tgid)))
        return
    raw = message.text.strip()
    # Убираем @ если написал с ним
    username = raw.lstrip("@").strip()
    # Валидация: 5–32 символа, только a-z A-Z 0-9 и _
    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", username):
        await message.answer(gt("invalid_username", lang), parse_mode="Markdown")
        return
    await state.update_data(username=username)
    await state.set_state(Checkout.waiting_phone)
    await message.answer(gt("enter_phone", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


# ── Шаг 3: Телефон ────────────────────────────────────────────────────────────
@router.message(Checkout.waiting_phone)
async def co_phone(message: Message, state: FSMContext):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear()
        await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, is_admin(tgid)))
        return
    # Убираем пробелы, дефисы, скобки
    phone_raw = re.sub(r"[\s\-\(\)]", "", message.text.strip())
    # Убираем префикс +372 или 372
    phone_raw = re.sub(r"^\+?372", "", phone_raw)
    # Эстонский номер: ровно 8 цифр, начинается с 3,4,5,6,7,8
    if not re.fullmatch(r"[3-8]\d{7}", phone_raw):
        await message.answer(gt("invalid_phone", lang), parse_mode="Markdown")
        return
    await state.update_data(phone=phone_raw)
    await state.set_state(Checkout.waiting_address)
    # Show saved addresses if user has any
    addrs = await get_saved_addresses(tgid)
    if addrs:
        addr_prompt = {
            "ru": "📍 Выберите сохранённый район или введите новый:",
            "en": "📍 Choose a saved area or enter a new one:",
            "et": "📍 Valige salvestatud piirkond või sisestage uus:",
        }.get(lang, "📍 Choose or enter area:")
        await message.answer(addr_prompt, reply_markup=kb_saved_addresses(addrs, lang), parse_mode="Markdown")
    else:
        await message.answer(gt("enter_address", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


# ── Шаг 4: Район/адрес ───────────────────────────────────────────────────────
@router.callback_query(Checkout.waiting_address, F.data.startswith("addr:use:"))
async def co_addr_pick(callback: CallbackQuery, state: FSMContext):
    """User picked a saved address."""
    addr_id = int(callback.data.split(":")[2])
    tgid    = callback.from_user.id
    lang    = await get_user_language(tgid)
    addrs   = await get_saved_addresses(tgid)
    chosen  = next((a for a in addrs if a["id"] == addr_id), None)
    if not chosen:
        await callback.answer(gt("error", lang), show_alert=True); return
    await state.update_data(address=chosen["address"])
    await callback.answer()
    await _finish_address(callback.message, state, tgid, lang)

@router.callback_query(Checkout.waiting_address, F.data == "addr:new")
async def co_addr_new(callback: CallbackQuery, state: FSMContext):
    lang = await get_user_language(callback.from_user.id)
    prompts = {"ru": gt("enter_address", lang), "en": gt("enter_address", lang), "et": gt("enter_address", lang)}
    await callback.message.answer(gt("enter_address", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")
    await callback.answer()

@router.message(Checkout.waiting_address)
async def co_address(message: Message, state: FSMContext):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear()
        await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, is_admin(tgid)))
        return
    address = message.text.strip()
    await state.update_data(address=address)
    # Auto-save if it's a new address (ask in background — just save silently)
    data = await state.get_data()
    addrs = await get_saved_addresses(tgid)
    existing = [a["address"] for a in addrs]
    if address not in existing and len(addrs) < 5:
        await save_address(tgid, address[:25], address)
    await _finish_address(message, state, tgid, lang)

async def _finish_address(msg_or_message, state: FSMContext, tgid: int, lang: str):
    from aiogram.types import Message as Msg
    await state.update_data()  # ensure data saved
    await state.set_state(Checkout.waiting_confirm)
    data = await state.get_data()
    raw_total = cart_total(tgid)  # used by _finish_address via state
    disc = data.get("discount_pct", 0)
    final_total, saved = apply_discount(raw_total, disc)
    await state.update_data(final_total=final_total, saved=saved)

    discount_line = ""
    if disc > 0:
        if lang == "ru":
            discount_line = f"\n🎁 Скидка *{disc}%*: −{saved:.2f} €"
        elif lang == "en":
            discount_line = f"\n🎁 Discount *{disc}%*: −{saved:.2f} €"
        else:
            discount_line = f"\n🎁 Allahindlus *{disc}%*: −{saved:.2f} €"

    await message.answer(
        gt("order_confirm", lang,
           name=data["cname"],
           username=data["username"],
           phone=data["phone"],
           address=data["address"],
           total=f"{final_total:.2f}") + discount_line,
        reply_markup=kb_confirm(lang), parse_mode="Markdown"
    )


@router.callback_query(Checkout.waiting_confirm, F.data == "order:reenter")
async def cb_reenter(callback: CallbackQuery, state: FSMContext):
    lang = await get_user_language(callback.from_user.id)
    await state.set_state(Checkout.waiting_name)
    await callback.message.answer(gt("enter_name", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(Checkout.waiting_confirm, F.data == "order:confirm")
async def cb_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    data = await state.get_data()
    its        = cart_items(tgid)
    total      = data.get("final_total") or cart_total(tgid)
    disc       = data.get("discount_pct", 0)
    saved      = data.get("saved", 0.0)
    try:
        oid = await create_order(
            tgid, total,
            data["cname"], data["username"], data["phone"], data["address"]
        )
    except Exception as e:
        log.error("create_order failed for user %s: %s", tgid, e)
        await state.clear()
        await callback.message.answer(gt("error", lang), reply_markup=kb_menu(lang, is_admin(tgid)))
        await callback.answer()
        return
    for it in its:
        await add_order_item(oid, it["pid"], it["qty"], it["price"])
    clear_cart(tgid)
    await state.clear()

    await callback.message.answer(
        gt("order_placed", lang, order_id=oid),
        reply_markup=kb_menu(lang, is_admin(tgid)), parse_mode="Markdown"
    )
    await callback.message.answer(
        build_receipt(oid, data["cname"], data["username"], data["phone"],
                      data["address"], its, total, lang, disc, saved),
        parse_mode="Markdown"
    )
    for aid in ADMIN_IDS:
        try:
            discount_note = f"\n🎁 Скидка {disc}%: −{saved:.2f} €" if disc > 0 else ""
            await bot.send_message(
                aid,
                gt("new_order_admin", "ru",
                   order_id=oid, name=data["cname"],
                   username=data["username"], phone=data["phone"],
                   address=data["address"], total=f"{total:.2f}") + discount_note,
                parse_mode="Markdown"
            )
        except Exception:
            pass

    # Уведомить реферера если это первый заказ приглашённого
    ref = await get_unpaid_referral(tgid)
    if ref:
        rtid = ref["user_id"]
        await mark_referral_bonus_paid(rtid, tgid)
        rl   = await get_user_language(rtid)
        # Считаем новую скидку реферера
        new_cnt  = await count_referrals(rtid)
        new_disc = get_referral_discount(new_cnt)
        notify = {
            "ru": f"🎉 Ваш друг сделал первый заказ!\nТеперь ваша скидка: *{new_disc}%*",
            "en": f"🎉 Your friend placed their first order!\nYour discount is now: *{new_disc}%*",
            "et": f"🎉 Teie sõber tegi esimese tellimuse!\nTeie allahindlus on nüüd: *{new_disc}%*",
        }.get(rl, "")
        try:
            await bot.send_message(rtid, notify, parse_mode="Markdown")
        except Exception:
            pass
    await callback.answer()
