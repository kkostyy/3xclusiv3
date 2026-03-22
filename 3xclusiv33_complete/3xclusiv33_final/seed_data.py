#!/usr/bin/env python3
import asyncio, os
from database.db import init_db, add_product
from config import DATABASE_PATH

PRODUCTS = [
    ("Летнее платье",    29.99, "clothes",     "Лёгкое платье, размеры S-XL", ""),
    ("Джинсы slim-fit",  34.99, "clothes",     "Классические зауженные джинсы", ""),
    ("Оверсайз худи",    24.99, "clothes",     "Уютное худи унисекс", ""),
    ("Льняная рубашка",  19.99, "clothes",     "Дышащая летняя рубашка", ""),
    ("Белые кроссовки",  45.99, "shoes",       "Повседневные кроссовки 36-45", ""),
    ("Кожаные ботинки",  69.99, "shoes",       "Ботинки на молнии", ""),
    ("Сандалии",         22.99, "shoes",       "Удобные плоские сандалии", ""),
    ("Холщовая сумка",   14.99, "accessories", "Экологичная сумка-шопер", ""),
    ("Золотые серьги",    8.99, "accessories", "Гипоаллергенная сталь", ""),
    ("Бейсболка",        12.99, "accessories", "Регулируемая кепка", ""),
]

async def seed():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    await init_db()
    for name, price, cat, desc, photo in PRODUCTS:
        pid = await add_product(name, price, cat, desc, photo)
        print(f"  ✅ #{pid}: {name} ({cat}) — {price}€")
    print("\n✅ Товары добавлены!")

if __name__ == "__main__":
    asyncio.run(seed())
