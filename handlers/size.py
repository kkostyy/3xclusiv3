# handlers/size.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import get_user_language
from keyboards import kb_cancel, kb_menu
from locales import gt
from states import SizeRecommendation
from utils import recommend_size, is_admin

router = Router()
def _is_cancel(t): return t in [gt("❌ Отмена", l) for l in ("ru","en","et")]


@router.message(F.text.func(lambda t: t in [gt("📏 Размер", l) for l in ("ru","en","et")]))
async def cmd_size(message: Message, state: FSMContext):
    lang = await get_user_language(message.from_user.id)
    await state.set_state(SizeRecommendation.waiting_height)
    await message.answer(gt("size_intro", lang) + "\n\n" + gt("enter_height", lang),
                         reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(SizeRecommendation.waiting_height)
async def size_height(message: Message, state: FSMContext):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear(); await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, is_admin(tgid))); return
    try:
        h = float(message.text.replace(",", "."))
        if not (100 <= h <= 250): raise ValueError
    except ValueError:
        await message.answer(gt("invalid_number", lang)); return
    await state.update_data(h=h); await state.set_state(SizeRecommendation.waiting_weight)
    await message.answer(gt("enter_weight", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(SizeRecommendation.waiting_weight)
async def size_weight(message: Message, state: FSMContext):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear(); await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, is_admin(tgid))); return
    try:
        w = float(message.text.replace(",", "."))
        if not (20 <= w <= 300): raise ValueError
    except ValueError:
        await message.answer(gt("invalid_number", lang)); return
    data = await state.get_data()
    size = recommend_size(data["h"], w)
    await state.clear()
    await message.answer(gt("size_result", lang, size=size, h=int(data["h"]), w=int(w)),
                         reply_markup=kb_menu(lang, is_admin(tgid)), parse_mode="Markdown")
