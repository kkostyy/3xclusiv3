# handlers/referral.py
from aiogram import Router, F
from aiogram.types import Message
from database import get_user_language, count_referrals, get_user
from locales import gt
from utils import ref_link, is_admin, get_referral_discount
from config import REFERRAL_TIERS, REFERRAL_MAX_DISCOUNT

router = Router()


def _tier_progress(count: int, lang: str) -> str:
    """Строка с прогрессом по уровням скидки."""
    lines = []
    labels = {"ru": "друг(ов)", "en": "friend(s)", "et": "sõber(a)"}
    word = labels.get(lang, "friend(s)")
    for threshold, pct in REFERRAL_TIERS:
        if count >= threshold:
            mark = "✅"
        else:
            mark = "⬜"
        lines.append(f"{mark} {threshold} {word} → *{pct}%*")
    return "\n".join(lines)


@router.message(F.text.func(lambda t: t in [gt("🔗 Рефералы", l) for l in ("ru", "en", "et")]))
async def cmd_referral(message: Message):
    tgid = message.from_user.id
    lang = await get_user_language(tgid)
    me   = await message.bot.get_me()
    link = ref_link(me.username, tgid)
    user = await get_user(tgid)
    cnt  = await count_referrals(tgid)
    disc = get_referral_discount(cnt)
    progress = _tier_progress(cnt, lang)

    # Следующий уровень
    next_tier = None
    for threshold, pct in REFERRAL_TIERS:
        if cnt < threshold:
            next_tier = (threshold, pct)
            break

    if lang == "ru":
        next_info = (
            f"➡️ До следующего уровня: ещё *{next_tier[0] - cnt}* чел. → *{next_tier[1]}%*"
            if next_tier else f"🏆 Максимальная скидка достигнута: *{REFERRAL_MAX_DISCOUNT}%*!"
        )
        text = (
            f"🔗 *Реферальная программа*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Приглашено: *{cnt}* чел.\n"
            f"💸 Ваша скидка: *{disc}%*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Уровни скидок:*\n{progress}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{next_info}\n\n"
            f"🔗 *Ваша ссылка:*\n`{link}`\n\n"
            f"_Скидка применяется автоматически при оформлении заказа_"
        )
    elif lang == "en":
        next_info = (
            f"➡️ Next level: *{next_tier[0] - cnt}* more → *{next_tier[1]}%*"
            if next_tier else f"🏆 Max discount reached: *{REFERRAL_MAX_DISCOUNT}%*!"
        )
        text = (
            f"🔗 *Referral Program*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Invited: *{cnt}* people\n"
            f"💸 Your discount: *{disc}%*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Discount tiers:*\n{progress}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{next_info}\n\n"
            f"🔗 *Your link:*\n`{link}`\n\n"
            f"_Discount applied automatically at checkout_"
        )
    else:  # et
        next_info = (
            f"➡️ Järgmine tase: veel *{next_tier[0] - cnt}* inimest → *{next_tier[1]}%*"
            if next_tier else f"🏆 Maksimaalne allahindlus: *{REFERRAL_MAX_DISCOUNT}%*!"
        )
        text = (
            f"🔗 *Suunamiseprogramm*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Kutsutud: *{cnt}* inimest\n"
            f"💸 Teie allahindlus: *{disc}%*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Allahindluse tasemed:*\n{progress}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{next_info}\n\n"
            f"🔗 *Teie link:*\n`{link}`\n\n"
            f"_Allahindlus rakendatakse kassas automaatselt_"
        )

    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
