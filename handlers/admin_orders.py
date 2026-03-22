# handlers/admin_orders.py
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user_language, get_all_orders, get_order, get_order_items, update_order_status
from keyboards import kb_orders_list, kb_statuses, kb_rating, status_text
from locales import gt
from utils import is_admin
from config import ADMIN_IDS

log = logging.getLogger(__name__)
router = Router()


@router.message(F.text.func(lambda t: t in [gt("📋 Заказы", l) for l in ("ru","en","et")]))
async def cmd_admin_orders(message: Message):
    if not is_admin(message.from_user.id): return
    lang   = await get_user_language(message.from_user.id)
    orders = await get_all_orders()
    if not orders:
        await message.answer(gt("no_orders_admin", lang)); return
    await message.answer(f"📋 *Все заказы ({len(orders)} шт.):*",
                         reply_markup=kb_orders_list(orders, lang), parse_mode="Markdown")


@router.callback_query(F.data.startswith("adminorder:"))
async def cb_order_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    oid  = int(callback.data.split(":")[1])
    lang = await get_user_language(callback.from_user.id)
    o    = await get_order(oid)
    if not o:
        await callback.answer(gt("order_not_found", lang), show_alert=True); return

    items = await get_order_items(oid)
    rows  = "\n".join(f"  • {i['name']} x{i['quantity']} = {i['price']*i['quantity']:.2f}€" for i in items)
    tg_username = o['tg_username'] or '—'
    price_line = f"💰 {o['total_price']:.2f} €"
    if o['adjusted_price']:
        price_line += f"\n💲 Скорр. цена: *{o['adjusted_price']:.2f} €* ⏳ ожидает ответа"
        if o['adjustment_reason']:
            price_line += f"\n📝 Причина: _{o['adjustment_reason']}_"
    text  = (
        f"📦 *Заказ #{oid}*\n"
        f"👤 {o['customer_name']}\n"
        f"📱 @{tg_username}\n"
        f"📞 {o['phone']}\n"
        f"📍 {o['address']}\n"
        f"🆔 `{o['telegram_id']}`\n"
        f"📊 {status_text(o['status'], lang)}\n"
        f"{price_line}\n"
        f"📅 {str(o['created_at'])[:10]}\n\n"
        f"🛍 Товары:\n{rows}"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb_statuses(oid, lang, buyer_tgid=o["telegram_id"]))
    await callback.answer()


@router.callback_query(F.data.startswith("setstatus:"))
async def cb_set_status(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id): return
    _, oid_str, new_status = callback.data.split(":")
    oid  = int(oid_str)
    lang = await get_user_language(callback.from_user.id)
    await update_order_status(oid, new_status)

    order = await get_order(oid)
    if order:
        uid   = order["telegram_id"]
        ul    = await get_user_language(uid)
        stext = status_text(new_status, ul)
        notify = gt("status_updated", ul, order_id=oid, status=stext)
        if new_status == "arrived":
            notify += gt("arrived_note", ul)
        try:
            await bot.send_message(uid, notify, parse_mode="Markdown")
        except Exception:
            pass
        if new_status == "delivered":
            try:
                await bot.send_message(uid, gt("rate_order", ul, order_id=oid),
                                        reply_markup=kb_rating(oid), parse_mode="Markdown")
            except Exception:
                pass

    await callback.message.edit_text(gt("status_changed", lang))
    await callback.answer()


@router.callback_query(F.data.startswith("cancelorder:"))
async def cb_cancel_order(callback: CallbackQuery, bot: Bot):
    oid  = int(callback.data.split(":")[1])
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    o    = await get_order(oid)
    if not o:
        await callback.answer(gt("order_not_found", lang), show_alert=True); return
    if o["status"] not in ("searching", "ordered"):
        cant_cancel = {"ru": "❌ Нельзя отменить на этом этапе.", "en": "❌ Cannot cancel at this stage.", "et": "❌ Selles etapis ei saa tühistada."}.get(lang, "❌ Cannot cancel.")
        await callback.answer(cant_cancel, show_alert=True)
        return

    await update_order_status(oid, "cancelled")
    ul = await get_user_language(o["telegram_id"])
    cancel_text = {"ru": f"✅ Заказ #{oid} отменён.", "en": f"✅ Order #{oid} cancelled.", "et": f"✅ Tellimus #{oid} tühistatud."}.get(ul, f"✅ Order #{oid} cancelled.")
    await callback.message.edit_text(cancel_text)
    for aid in ADMIN_IDS:
        try:
            await bot.send_message(aid, f"⚠️ Пользователь `{tgid}` отменил заказ #{oid}.", parse_mode="Markdown")
        except Exception:
            pass
    await callback.answer()


class AdminWriteBuyer(StatesGroup):
    waiting_message = State()


@router.callback_query(F.data.startswith("writebuyer:"))
async def cb_write_buyer_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    parts   = callback.data.split(":")
    oid     = int(parts[1])
    uid     = int(parts[2])
    lang    = await get_user_language(callback.from_user.id)
    from keyboards import kb_cancel
    await state.update_data(wb_oid=oid, wb_uid=uid)
    await state.set_state(AdminWriteBuyer.waiting_message)
    prompts = {
        "ru": f"✉️ *Сообщение покупателю — Заказ #{oid}*\n\nНапишите сообщение:",
        "en": f"✉️ *Message to buyer — Order #{oid}*\n\nWrite your message:",
        "et": f"✉️ *Sõnum ostjale — Tellimus #{oid}*\n\nKirjutage sõnum:",
    }
    await callback.message.answer(prompts.get(lang, prompts["en"]),
                                   reply_markup=kb_cancel(lang), parse_mode="Markdown")
    await callback.answer()


@router.message(AdminWriteBuyer.waiting_message)
async def wb_send(message: Message, state: FSMContext, bot: Bot):
    lang = await get_user_language(message.from_user.id)
    if message.text in [gt("❌ Отмена", l) for l in ("ru","en","et")]:
        await state.clear()
        from keyboards import kb_menu
        await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True))
        return

    data = await state.get_data()
    oid  = data["wb_oid"]
    uid  = data["wb_uid"]
    ul   = await get_user_language(uid)

    headers = {
        "ru": f"🏪 *Сообщение от продавца — Заказ #{oid}*\n━━━━━━━━━━━━━━━━━━━\n",
        "en": f"🏪 *Message from seller — Order #{oid}*\n━━━━━━━━━━━━━━━━━━━\n",
        "et": f"🏪 *Sõnum müüjalt — Tellimus #{oid}*\n━━━━━━━━━━━━━━━━━━━\n",
    }

    try:
        if message.photo:
            await bot.send_photo(uid, message.photo[-1].file_id,
                                  caption=headers.get(ul, headers["en"]) + (message.caption or ""),
                                  parse_mode="Markdown")
        else:
            await bot.send_message(uid, headers.get(ul, headers["en"]) + message.text,
                                    parse_mode="Markdown")
        await state.clear()
        from keyboards import kb_menu
        sent_ok = {"ru": f"✅ Сообщение доставлено покупателю (заказ #{oid})",
                   "en": f"✅ Message delivered to buyer (order #{oid})",
                   "et": f"✅ Sõnum edastatud ostjale (tellimus #{oid})"}
        await message.answer(sent_ok.get(lang, sent_ok["en"]), reply_markup=kb_menu(lang, True))
    except Exception as e:
        log.error("Cannot send to buyer %s: %s", uid, e)
        await state.clear()
        from keyboards import kb_menu
        await message.answer(gt("error", lang), reply_markup=kb_menu(lang, True))
