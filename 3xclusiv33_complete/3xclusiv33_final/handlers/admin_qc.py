# handlers/admin_qc.py
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import get_user_language, get_order, create_qc_request
from keyboards import kb_qc, kb_cancel, kb_menu
from locales import gt
from states import AdminSendQC
from utils import is_admin

log = logging.getLogger(__name__)
router = Router()

def _is_cancel(t): return t in [gt("❌ Отмена", l) for l in ("ru","en","et")]


@router.message(F.text.func(lambda t: t in [gt("📸 QC", l) for l in ("ru","en","et")]))
async def cmd_admin_qc(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    lang = await get_user_language(message.from_user.id)
    await state.set_state(AdminSendQC.waiting_order_id)
    await message.answer(gt("enter_order_id_qc", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(AdminSendQC.waiting_order_id)
async def qc_order_id(message: Message, state: FSMContext):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear(); await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, True)); return
    try:
        oid = int(message.text.strip())
    except ValueError:
        await message.answer(gt("invalid_number", lang)); return
    o = await get_order(oid)
    if not o:
        await message.answer(gt("order_not_found", lang)); return
    await state.update_data(qc_oid=oid, qc_uid=o["telegram_id"])
    await state.set_state(AdminSendQC.waiting_photo)
    await message.answer(gt("send_qc_photo", lang), reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(AdminSendQC.waiting_photo, F.photo)
async def qc_photo(message: Message, state: FSMContext, bot: Bot):
    tgid  = message.from_user.id; lang = await get_user_language(tgid)
    photo = message.photo[-1].file_id; data = await state.get_data()
    oid   = data["qc_oid"]; uid = data["qc_uid"]
    qc_id = await create_qc_request(oid, photo)
    ul    = await get_user_language(uid)
    try:
        await bot.send_photo(uid, photo,
                             caption=gt("qc_received", ul, order_id=oid),
                             reply_markup=kb_qc(qc_id, ul), parse_mode="Markdown")
        await message.answer(gt("qc_sent", lang), reply_markup=kb_menu(lang, True))
    except Exception as e:
        log.error("QC send error to user %s: %s", uid, e)
        await message.answer(gt("error", lang), reply_markup=kb_menu(lang, True))
    await state.clear()
