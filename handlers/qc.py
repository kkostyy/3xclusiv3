# handlers/qc.py
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database import get_user_language, get_qc_request, update_qc_status
from locales import gt
from config import ADMIN_IDS

log = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("qc:"))
async def cb_qc(callback: CallbackQuery, bot: Bot):
    _, action, qc_id_str = callback.data.split(":")
    qc_id = int(qc_id_str)
    tgid  = callback.from_user.id
    lang  = await get_user_language(tgid)

    qc = await get_qc_request(qc_id)
    if not qc:
        await callback.answer(gt("error", lang), show_alert=True); return

    order_id = qc["order_id"]
    if action == "accept":
        await update_qc_status(qc_id, "accepted")
        await callback.message.edit_caption(caption=gt("qc_accepted", lang), parse_mode="Markdown")
        icon = "✅"; verb = "принял"
    else:
        await update_qc_status(qc_id, "rejected")
        await callback.message.edit_caption(caption=gt("qc_rejected", lang), parse_mode="Markdown")
        icon = "❌"; verb = "отклонил"

    for aid in ADMIN_IDS:
        try:
            await bot.send_message(aid, f"{icon} Пользователь `{tgid}` {verb} QC для заказа #{order_id}.", parse_mode="Markdown")
        except Exception:
            pass
    await callback.answer()
