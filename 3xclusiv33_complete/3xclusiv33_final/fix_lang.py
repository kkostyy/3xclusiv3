import asyncio
import aiosqlite

async def fix():
    async with aiosqlite.connect("data/clothing_store.db") as db:
        await db.execute("UPDATE users SET language = 'ru' WHERE telegram_id = 6057821265")
        await db.commit()
        print("✅ Язык изменён на русский!")

asyncio.run(fix())
