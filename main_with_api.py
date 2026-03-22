#!/usr/bin/env python3
# main_with_api.py — запускает Telegram бот + FastAPI одновременно

import asyncio
import logging
import sys
import os

# ── Railway fix: убеждаемся что /app в sys.path ──────────────────────────────
# Railway запускает из /app, но иногда рабочий каталог не добавлен в path.
# Добавляем директорию самого файла — так database/, handlers/ всегда найдутся.
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)  # рабочий каталог = папка с main_with_api.py
# ─────────────────────────────────────────────────────────────────────────────

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, migrate_db
from handlers import all_routers
from api import app as fastapi_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


async def run_bot() -> None:
    """Запускает Telegram бот с polling."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан! Добавьте в .env или переменные окружения.")
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Инициализация БД
    await init_db()
    await migrate_db()

    # Получаем username бота и сохраняем в env (нужен api.py для реферальных ссылок)
    me = await bot.get_me()
    os.environ["BOT_USERNAME"] = me.username or ""
    logger.info("✅ Бот @%s запущен", me.username)

    # Уведомляем админов
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"✅ *3xclusiv33* запущен!\n\n"
                f"🤖 Бот: @{me.username}\n"
                f"🌐 Mini App: деплой на Vercel\n"
                f"🔧 API: порт {os.getenv('PORT', '8080')}",
            )
        except Exception as e:
            logger.warning("Не удалось уведомить admin %s: %s", admin_id, e)

    # Подключаем роутеры
    for router in all_routers:
        dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def run_api() -> None:
    """Запускает FastAPI сервер (отдаёт /api/* endpoints и miniapp.html как fallback)."""
    port = int(os.getenv("PORT", 8080))
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.info("🌐 API запущен на порту %d", port)
    await server.serve()


async def main() -> None:
    """Запускает бот и API параллельно."""
    logger.info("🚀 Запуск 3xclusiv33...")
    await asyncio.gather(
        run_bot(),
        run_api(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Остановлено вручную")
