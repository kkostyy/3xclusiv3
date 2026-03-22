# handlers/common.py
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database import get_user, create_user, update_user_language, get_user_language, count_user_orders, create_referral
from keyboards import kb_lang, kb_menu, kb_more, kb_settings
from locales import gt, LANG_NAMES
from states import LanguageSelection
from utils import is_admin

logger = logging.getLogger(__name__)
router = Router()

# Helper: all translations of a key
def _all(key): return [gt(key, l) for l in ("ru","en","et")]
def _is_cancel(t): return t in _all("❌ Отмена")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    tgid = message.from_user.id
    args = message.text.split()
    ref_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1][4:])
            if ref_id == tgid: ref_id = None
        except ValueError: pass

    user = await get_user(tgid)
    if user is None:
        await state.update_data(ref_id=ref_id)
        await state.set_state(LanguageSelection.choosing)
        await message.answer("🌍 Choose language / Выберите язык / Valige keel:", reply_markup=kb_lang())
    else:
        lang = user["language"]
        await message.answer(gt("welcome", lang), reply_markup=kb_menu(lang, is_admin(tgid)), parse_mode="Markdown")


@router.callback_query(LanguageSelection.choosing, F.data.startswith("lang:"))
async def cb_lang_new(callback: CallbackQuery, state: FSMContext):
    lang  = callback.data.split(":")[1]
    tgid  = callback.from_user.id
    name  = callback.from_user.full_name or f"User_{tgid}"
    data  = await state.get_data()
    ref_id = data.get("ref_id")
    await create_user(tgid, name, lang, ref_id)
    if ref_id and ref_id != tgid:
        await create_referral(ref_id, tgid)
        ref = await get_user(ref_id)
        if ref:
            await callback.message.answer(gt("referral_welcome", lang, name=ref["name"] or f"#{ref_id}"), parse_mode="Markdown")
    await state.clear()
    try: await callback.message.delete()
    except: pass
    await callback.message.answer(gt("welcome", lang), reply_markup=kb_menu(lang, is_admin(tgid)), parse_mode="Markdown")
    await callback.answer(gt("language_set", lang))

# handlers/common.py — добавьте команду /admin
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="⚙️ Панель управления",
            web_app=WebAppInfo(url="https://your-project.vercel.app/admin")
        )
    ]])
    await message.answer("Панель владельца", reply_markup=kb)


@router.callback_query(F.data.startswith("lang:"))
async def cb_lang_change(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    tgid = callback.from_user.id
    await update_user_language(tgid, lang)
    await state.clear()
    try: await callback.message.delete()
    except: pass
    await callback.message.answer(gt("welcome", lang), reply_markup=kb_menu(lang, is_admin(tgid)), parse_mode="Markdown")
    await callback.answer(gt("language_set", lang))


@router.message(F.text.func(lambda t: t in [gt("⚙️ Настройки", l) for l in ("ru","en","et")]))
async def cmd_settings(message: Message):
    lang = await get_user_language(message.from_user.id)
    await message.answer(gt("settings_menu", lang), reply_markup=kb_settings(lang), parse_mode="Markdown")


@router.callback_query(F.data == "settings:lang")
async def cb_settings_lang(callback: CallbackQuery):
    await callback.message.edit_text("🌍 Choose language / Выберите язык / Valige keel:", reply_markup=kb_lang())
    await callback.answer()


@router.callback_query(F.data == "settings:profile")
async def cb_settings_profile(callback: CallbackQuery):
    tgid = callback.from_user.id
    lang = await get_user_language(tgid)
    user = await get_user(tgid)
    if not user:
        await callback.answer(gt("error", lang), show_alert=True); return
    cnt  = await count_user_orders(tgid)
    text = gt("profile_info", lang,
              tg_id=tgid, name=user["name"] or "—",
              lang=LANG_NAMES.get(lang, lang),
              balance=f"{user['balance']:.2f}", orders=cnt)
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()


@router.message(F.text.func(lambda t: t in [gt("🏠 Главное меню", l) for l in ("ru","en","et")]))
async def cmd_main_menu(message: Message, state: FSMContext):
    await state.clear()
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    await message.answer(gt("welcome", lang), reply_markup=kb_menu(lang, is_admin(tgid)), parse_mode="Markdown")


@router.message(F.text.func(lambda t: t in [gt("☰ Ещё", l) for l in ("ru","en","et")]))
async def cmd_more(message: Message):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    await message.answer("☰", reply_markup=kb_more(lang, is_admin(tgid)))


@router.message(F.text.func(lambda t: t in [gt("🔙 Назад", l) for l in ("ru","en","et")]))
async def cmd_back(message: Message, state: FSMContext):
    await state.clear()
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    await message.answer(gt("welcome", lang), reply_markup=kb_menu(lang, is_admin(tgid)), parse_mode="Markdown")


@router.message(Command("cancel"))
@router.message(F.text.func(_is_cancel))
async def cmd_cancel(message: Message, state: FSMContext):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    await state.clear()
    await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, is_admin(tgid)))
