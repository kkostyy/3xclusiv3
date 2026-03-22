# handlers/price_adjust.py
# Флоу: админ видит заказ → нажимает "Скорректировать цену" →
#        вводит новую цену (макс +20%) → вводит причину →
#        покупатель получает уведомление с кнопками "Принять / Отменить"
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import (get_user_language, get_order, get_order_items,
                      set_price_adjustment, reject_price_adjustment)
from keyboards import kb_cancel, kb_menu, kb_price_decision
from states import AdminPriceAdjust
from utils import is_admin
from locales import gt

log = logging.getLogger(__name__)
router = Router()

MAX_ADJUSTMENT_PCT = 20  # максимум +20% от оригинальной цены


# ── Шаг 1: Админ нажал "Скорректировать цену" ────────────────────────────────
@router.callback_query(F.data.startswith("adjprice:"))
async def cb_adj_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True); return

    oid  = int(callback.data.split(":")[1])
    lang = await get_user_language(callback.from_user.id)
    o    = await get_order(oid)
    if not o:
        await callback.answer(gt("order_not_found", lang), show_alert=True); return

    original = o["total_price"]
    max_price = round(original * (1 + MAX_ADJUSTMENT_PCT / 100), 2)

    await state.update_data(adj_oid=oid, original_price=original, max_price=max_price)
    await state.set_state(AdminPriceAdjust.waiting_price)

    await callback.message.answer(
        f"💲 *Корректировка цены — Заказ #{oid}*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Текущая цена: *{original:.2f} €*\n"
        f"⚠️ Максимум +{MAX_ADJUSTMENT_PCT}%: *{max_price:.2f} €*\n\n"
        f"Введите новую цену (€):",
        reply_markup=kb_cancel(lang), parse_mode="Markdown"
    )
    await callback.answer()


# ── Шаг 2: Новая цена ─────────────────────────────────────────────────────────
@router.message(AdminPriceAdjust.waiting_price)
async def adj_price(message: Message, state: FSMContext):
    lang = await get_user_language(message.from_user.id)

    if message.text in [gt("❌ Отмена", l) for l in ("ru","en","et")]:
        await state.clear()
        await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True))
        return

    try:
        new_price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число, например: 35.50"); return

    data = await state.get_data()
    original  = data["original_price"]
    max_price = data["max_price"]

    if new_price <= original:
        await message.answer(
            f"❌ Новая цена должна быть *выше* текущей ({original:.2f} €).",
            parse_mode="Markdown"
        ); return

    if new_price > max_price:
        await message.answer(
            f"❌ Максимально допустимо *{max_price:.2f} €* (+{MAX_ADJUSTMENT_PCT}%).\n"
            f"Введите цену не больше {max_price:.2f} €:",
            parse_mode="Markdown"
        ); return

    await state.update_data(new_price=new_price)
    await state.set_state(AdminPriceAdjust.waiting_reason)

    pct = round((new_price - original) / original * 100, 1)
    await message.answer(
        f"✅ Новая цена: *{new_price:.2f} €* (+{pct}%)\n\n"
        f"📝 Теперь введите *причину* корректировки\n"
        f"_(например: район Ласнамяэ, срочная доставка)_:",
        reply_markup=kb_cancel(lang), parse_mode="Markdown"
    )


# ── Шаг 3: Причина → отправить покупателю ────────────────────────────────────
@router.message(AdminPriceAdjust.waiting_reason)
async def adj_reason(message: Message, state: FSMContext, bot: Bot):
    lang = await get_user_language(message.from_user.id)

    if message.text in [gt("❌ Отмена", l) for l in ("ru","en","et")]:
        await state.clear()
        await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True))
        return

    reason = message.text.strip()
    if len(reason) < 3:
        await message.answer("❌ Введите причину (минимум 3 символа):"); return

    data      = await state.get_data()
    oid       = data["adj_oid"]
    original  = data["original_price"]
    new_price = data["new_price"]
    pct       = round((new_price - original) / original * 100, 1)

    # Сохраняем в БД, статус остаётся 'searching' пока покупатель не ответит
    await set_price_adjustment(oid, new_price, reason)

    # Получаем данные покупателя
    o  = await get_order(oid)
    if not o:
        await state.clear()
        await message.answer(gt("error", lang), reply_markup=kb_menu(lang, True)); return

    uid = o["telegram_id"]
    ul  = await get_user_language(uid)

    # Уведомление покупателю
    notif_texts = {
        "ru": (
            f"⚠️ *Изменение цены — Заказ #{oid}*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Старая цена: *{original:.2f} €*\n"
            f"💲 Новая цена: *{new_price:.2f} €* (+{pct}%)\n\n"
            f"📝 Причина: _{reason}_\n\n"
            f"Пожалуйста, примите решение:"
        ),
        "en": (
            f"⚠️ *Price update — Order #{oid}*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Original price: *{original:.2f} €*\n"
            f"💲 New price: *{new_price:.2f} €* (+{pct}%)\n\n"
            f"📝 Reason: _{reason}_\n\n"
            f"Please make your decision:"
        ),
        "et": (
            f"⚠️ *Hinna muutus — Tellimus #{oid}*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Algne hind: *{original:.2f} €*\n"
            f"💲 Uus hind: *{new_price:.2f} €* (+{pct}%)\n\n"
            f"📝 Põhjus: _{reason}_\n\n"
            f"Palun tehke otsus:"
        ),
    }

    try:
        await bot.send_message(
            uid,
            notif_texts.get(ul, notif_texts["en"]),
            reply_markup=kb_price_decision(oid, ul),
            parse_mode="Markdown"
        )
        await state.clear()
        await message.answer(
            f"✅ Покупатель уведомлён. Ожидаем ответа.",
            reply_markup=kb_menu(lang, True)
        )
    except Exception as e:
        log.error("Cannot notify buyer %s: %s", uid, e)
        await state.clear()
        await message.answer(gt("error", lang), reply_markup=kb_menu(lang, True))


# ── Покупатель: Принять новую цену ───────────────────────────────────────────
@router.callback_query(F.data.startswith("priceok:"))
async def cb_price_accept(callback: CallbackQuery, bot: Bot):
    oid  = int(callback.data.split(":")[1])
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    o    = await get_order(oid)
    if not o:
        await callback.answer(gt("error", lang), show_alert=True); return

    new_price = o["adjusted_price"]
    reason    = o["adjustment_reason"]

    # Принял — обновляем total_price на новую, убираем pending adjustment
    import aiosqlite
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE orders SET total_price=adjusted_price, status='ordered', "
            "adjusted_price=NULL, adjustment_reason=NULL WHERE id=?", (oid,)
        )
        await db.commit()

    accepted_texts = {
        "ru": f"✅ Вы приняли новую цену *{new_price:.2f} €*.\nЗаказ #{oid} подтверждён!",
        "en": f"✅ You accepted the new price *{new_price:.2f} €*.\nOrder #{oid} confirmed!",
        "et": f"✅ Nõustusite uue hinnaga *{new_price:.2f} €*.\nTellimus #{oid} kinnitatud!",
    }
    await callback.message.edit_text(accepted_texts.get(lang, accepted_texts["en"]), parse_mode="Markdown")

    # Уведомить админа
    from config import ADMIN_IDS
    for aid in ADMIN_IDS:
        try:
            await bot.send_message(
                aid,
                f"✅ Покупатель `{tgid}` принял скорректированную цену *{new_price:.2f} €* для заказа #{oid}.",
                parse_mode="Markdown"
            )
        except Exception:
            pass
    await callback.answer()


# ── Покупатель: Отклонить — отменить заказ ───────────────────────────────────
@router.callback_query(F.data.startswith("pricecancel:"))
async def cb_price_reject(callback: CallbackQuery, bot: Bot):
    oid  = int(callback.data.split(":")[1])
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    o    = await get_order(oid)
    if not o:
        await callback.answer(gt("error", lang), show_alert=True); return

    await reject_price_adjustment(oid)

    rejected_texts = {
        "ru": f"❌ Заказ #{oid} отменён.\nЕсли хотите — оформите новый заказ.",
        "en": f"❌ Order #{oid} cancelled.\nFeel free to place a new order.",
        "et": f"❌ Tellimus #{oid} tühistatud.\nSaate vajadusel uue tellimuse teha.",
    }
    await callback.message.edit_text(rejected_texts.get(lang, rejected_texts["en"]), parse_mode="Markdown")

    # Уведомить админа
    from config import ADMIN_IDS
    for aid in ADMIN_IDS:
        try:
            await bot.send_message(
                aid,
                f"❌ Покупатель `{tgid}` отклонил скорректированную цену для заказа #{oid}. Заказ отменён.",
                parse_mode="Markdown"
            )
        except Exception:
            pass
    await callback.answer()
