# handlers/support.py
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import get_user_language
from locales import gt
from utils import is_admin
from config import ADMIN_IDS

log = logging.getLogger(__name__)
router = Router()

_reply_to: dict[int, int] = {}


class SupportChat(StatesGroup):
    chatting = State()


def _reply_kb(uid):
    b = InlineKeyboardBuilder()
    b.button(text=f"↩️ Ответить #{uid}", callback_data=f"reply_to:{uid}")
    return b.as_markup()


@router.message(F.text.func(lambda t: t in [gt("💬 Продавец", l) for l in ("ru","en","et")]))
async def cmd_support(message: Message, state: FSMContext):
    lang = await get_user_language(message.from_user.id)
    _reply_to.pop(message.from_user.id, None)  # не в режиме ответа
    await state.set_state(SupportChat.chatting)
    await message.answer(gt("support_intro", lang), parse_mode="Markdown")


@router.message(SupportChat.chatting)
async def user_to_seller(message: Message, bot: Bot):
    tgid = message.from_user.id; lang = await get_user_language(tgid)
    name = message.from_user.full_name or f"User_{tgid}"

    # Выход через главное меню
    if message.text and message.text in [gt("🏠 Главное меню", l) for l in ("ru","en","et")]:
        return  # common.py обработает

    text = f"💬 *От покупателя*\n👤 {name} | 🆔 `{tgid}`\n━━━━━━━━━━━━━━\n{message.text or '[медиа]'}"
    ok = False
    for aid in ADMIN_IDS:
        try:
            if message.photo:
                await bot.send_photo(aid, message.photo[-1].file_id, caption=text, parse_mode="Markdown", reply_markup=_reply_kb(tgid))
            else:
                await bot.send_message(aid, text, parse_mode="Markdown", reply_markup=_reply_kb(tgid))
            ok = True
        except Exception as e:
            log.warning("Cannot send to admin %s: %s", aid, e)

    await message.answer(gt("support_sent", lang) if ok else gt("error", lang))


@router.callback_query(F.data.startswith("reply_to:"))
async def cb_reply_to(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True); return
    uid = int(callback.data.split(":")[1])
    _reply_to[callback.from_user.id] = uid
    await callback.message.answer(f"↩️ Reply mode: customer `{uid}`\nWrite your reply or /stopreply", parse_mode="Markdown")
    await callback.answer(f"Replying to #{uid}")


@router.message(F.from_user.func(lambda u: is_admin(u.id)) & F.text & ~F.text.startswith("/"))
async def admin_reply(message: Message, bot: Bot):
    aid = message.from_user.id
    # Пропускаем кнопки меню
    all_menu = set()
    for k in ("📦 Товары","📋 Заказы","📸 QC","⭐ Отзывы","🔗 Рефералы адм",
               "📊 Статистика","📈 Товары стат","📣 Рассылка","🚚 Доставка",
               "☰ Ещё","🔙 Назад","🏠 Главное меню","❌ Отмена"):
        for l in ("ru","en","et"): all_menu.add(gt(k, l))
    if message.text in all_menu: return

    uid = _reply_to.get(aid)
    if not uid: return

    try:
        ul = await get_user_language(uid)
        await bot.send_message(uid, f"{gt('support_reply_hdr', ul)}\n\n{message.text}", parse_mode="Markdown")
        await message.answer(f"✅ Доставлено покупателю `{uid}`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("stopreply"))
async def cmd_stopreply(message: Message):
    if not is_admin(message.from_user.id): return
    uid = _reply_to.pop(message.from_user.id, None)
    if uid:
        await message.answer(f"✅ Reply mode ended (customer: {uid}).")
    else:
        await message.answer("✅ Reply mode was not active.")
