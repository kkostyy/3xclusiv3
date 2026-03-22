#!/usr/bin/env python3
import os
import sys

# Railway path fix — должно быть ДО всех остальных импортов
sys.path.insert(0, '/app')

import asyncio
import logging

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
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def run_bot() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан!")
        return

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp  = Dispatcher(storage=MemoryStorage())

    await init_db()
    await migrate_db()

    me = await bot.get_me()
    os.environ["BOT_USERNAME"] = me.username or ""
    logger.info("✅ Бот @%s запущен", me.username)

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"✅ *3xclusiv33* запущен! Бот: @{me.username}")
        except Exception:
            pass

    for router in all_routers:
        dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def run_api() -> None:
    port = int(os.getenv("PORT", 8080))
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)
    logger.info("🌐 API запущен на порту %d", port)
    await server.serve()


async def main() -> None:
    await asyncio.gather(run_bot(), run_api())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
