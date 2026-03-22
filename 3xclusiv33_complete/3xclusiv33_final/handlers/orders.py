# handlers/orders.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_user_language, get_user_orders, get_order_items, add_review
from keyboards import kb_rating, kb_menu, kb_cancel_order, status_text
from locales import gt
from states import Review
from utils import is_admin

log = logging.getLogger(__name__)
router = Router()


@router.message(F.text.func(lambda t: t in [gt("📦 Мои заказы", l) for l in ("ru","en","et")]))
async def cmd_orders(message: Message):
    tgid   = message.from_user.id
    lang   = await get_user_language(tgid)
    orders = await get_user_orders(tgid)
    if not orders:
        await message.answer(gt("no_orders", lang)); return

    for o in orders:
        items = await get_order_items(o["id"])
        rows  = "\n".join(f"  • {i['name']} × {i['quantity']} = {i['price']*i['quantity']:.2f} €" for i in items)
        text  = gt("order_card", lang, id=o["id"], date=str(o["created_at"])[:10],
                   status=status_text(o["status"], lang), total=f"{o['total_price']:.2f}")
        text += f"\n{rows}"

        if o["status"] == "delivered":
            await message.answer(text, parse_mode="Markdown", reply_markup=kb_rating(o["id"]))
        elif o["status"] in ("searching", "ordered"):
            await message.answer(text, parse_mode="Markdown", reply_markup=kb_cancel_order(o["id"], lang))
        else:
            await message.answer(text, parse_mode="Markdown")


@router.callback_query(F.data.startswith("rate:"))
async def cb_rate(callback: CallbackQuery, state: FSMContext):
    _, oid, stars = callback.data.split(":")
    lang = await get_user_language(callback.from_user.id)
    await state.update_data(r_order=int(oid), r_stars=int(stars))
    await state.set_state(Review.waiting_comment)
    await callback.message.edit_text(f"{'⭐'*int(stars)} ({stars}/5)\n\n{gt('enter_comment', lang)}", parse_mode="Markdown")
    await callback.answer()


@router.message(Review.waiting_comment)
async def review_comment(message: Message, state: FSMContext):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    data = await state.get_data()
    comment = "" if message.text == "/skip" else message.text
    await add_review(tgid, data["r_order"], data["r_stars"], comment)
    await state.clear()
    await message.answer(gt("review_saved", lang), reply_markup=kb_menu(lang, is_admin(tgid)), parse_mode="Markdown")
