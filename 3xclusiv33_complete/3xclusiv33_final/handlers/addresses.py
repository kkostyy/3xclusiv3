# handlers/addresses.py — сохранённые адреса встречи
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user_language, get_saved_addresses, save_address, delete_saved_address
from keyboards import kb_saved_addresses, kb_address_manage, kb_menu, kb_cancel
from locales import gt
from utils import is_admin

log = logging.getLogger(__name__)
router = Router()

_LANGS = ("ru", "en", "et")


class SaveAddress(StatesGroup):
    waiting_label   = State()
    waiting_address = State()


def _is_cancel(t): return t in [gt("❌ Отмена", l) for l in _LANGS]


ADDR_TITLES = {
    "ru": "📍 *Сохранённые адреса встречи*\n\nВыберите или добавьте новый район:",
    "en": "📍 *Saved meeting areas*\n\nChoose or add a new area:",
    "et": "📍 *Salvestatud kohtumiskohad*\n\nValige või lisage uus piirkond:",
}
ADDR_EMPTY = {
    "ru": "📍 *Сохранённые адреса*\n\nУ вас ещё нет сохранённых адресов.\n\nНажмите ✏️ Ввести новый чтобы добавить.",
    "en": "📍 *Saved addresses*\n\nYou have no saved addresses yet.\n\nPress ✏️ Enter new to add one.",
    "et": "📍 *Salvestatud aadressid*\n\nTeil pole veel salvestatud aadresse.\n\nVajutage ✏️ Sisesta uus lisamiseks.",
}


@router.message(F.text.func(lambda t: t in [gt("📍 Адреса", l) for l in _LANGS]))
async def cmd_addresses(message: Message):
    tgid  = message.from_user.id
    lang  = await get_user_language(tgid)
    addrs = await get_saved_addresses(tgid)
    title = ADDR_TITLES.get(lang, ADDR_TITLES["en"]) if addrs else ADDR_EMPTY.get(lang, ADDR_EMPTY["en"])
    await message.answer(title, reply_markup=kb_saved_addresses(addrs, lang), parse_mode="Markdown")


@router.callback_query(F.data == "addr:new")
async def cb_addr_new(callback: CallbackQuery, state: FSMContext):
    lang = await get_user_language(callback.from_user.id)
    prompts = {"ru": "🏷 Введите *название* для адреса (например: Центр, Работа, Дом):",
               "en": "🏷 Enter a *name* for this address (e.g. Center, Work, Home):",
               "et": "🏷 Sisestage aadressile *nimi* (nt Kesklinn, Töö, Kodu):"}
    await state.set_state(SaveAddress.waiting_label)
    await callback.message.answer(prompts.get(lang, prompts["en"]), reply_markup=kb_cancel(lang), parse_mode="Markdown")
    await callback.answer()


@router.message(SaveAddress.waiting_label)
async def sa_label(message: Message, state: FSMContext):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear()
        await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, is_admin(tgid))); return
    label = message.text.strip()[:30]
    await state.update_data(label=label)
    await state.set_state(SaveAddress.waiting_address)
    prompts = {"ru": f"📍 Теперь введите сам *адрес/район* для «{label}»:",
               "en": f"📍 Now enter the *address/area* for «{label}»:",
               "et": f"📍 Nüüd sisestage *aadress/piirkond* jaoks «{label}»:"}
    await message.answer(prompts.get(lang, prompts["en"]), reply_markup=kb_cancel(lang), parse_mode="Markdown")


@router.message(SaveAddress.waiting_address)
async def sa_address(message: Message, state: FSMContext):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    if _is_cancel(message.text):
        await state.clear()
        await message.answer(gt("cancelled_action", lang), reply_markup=kb_menu(lang, is_admin(tgid))); return
    data = await state.get_data()
    await save_address(tgid, data["label"], message.text.strip())
    await state.clear()
    addrs = await get_saved_addresses(tgid)
    saved_msg = {"ru": f"✅ Адрес «{data['label']}» сохранён!",
                 "en": f"✅ Address «{data['label']}» saved!",
                 "et": f"✅ Aadress «{data['label']}» salvestatud!"}
    await message.answer(
        saved_msg.get(lang, saved_msg["en"]),
        reply_markup=kb_saved_addresses(addrs, lang),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("addr:del:"))
async def cb_addr_delete(callback: CallbackQuery):
    addr_id = int(callback.data.split(":")[2])
    tgid    = callback.from_user.id
    lang    = await get_user_language(tgid)
    await delete_saved_address(addr_id, tgid)
    addrs = await get_saved_addresses(tgid)
    deleted = {"ru": "🗑 Адрес удалён", "en": "🗑 Address deleted", "et": "🗑 Aadress kustutatud"}
    await callback.answer(deleted.get(lang, ""), show_alert=False)
    title = ADDR_TITLES.get(lang, ADDR_TITLES["en"]) if addrs else ADDR_EMPTY.get(lang, ADDR_EMPTY["en"])
    await callback.message.edit_text(title, reply_markup=kb_saved_addresses(addrs, lang), parse_mode="Markdown")
