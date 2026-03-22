import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
SELLER_USERNAME: str = os.getenv("SELLER_USERNAME", "")  # Telegram username продавца без @
ADMIN_IDS: list[int] = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()]
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/store.db")
# Реферальные скидки по уровням (кол-во приглашённых -> скидка %)
REFERRAL_TIERS = [
    (1,  3),   # 1 друг  → 3%
    (2,  5),   # 2 друга → 5%
    (5,  10),  # 5 друзей → 10%
    (10, 15),  # 10 друзей → 15%
]
# Максимальная скидка
REFERRAL_MAX_DISCOUNT = 15

SIZE_CHART = {
    "XS": {"height": (148, 158), "weight": (40, 50)},
    "S":  {"height": (158, 165), "weight": (48, 58)},
    "M":  {"height": (165, 172), "weight": (56, 68)},
    "L":  {"height": (172, 180), "weight": (66, 80)},
    "XL": {"height": (178, 188), "weight": (78, 95)},
    "XXL":{"height": (186, 200), "weight": (92, 130)},
}
