from aiogram.fsm.state import State, StatesGroup

class LanguageSelection(StatesGroup):
    choosing = State()

class SizeRecommendation(StatesGroup):
    waiting_height = State()
    waiting_weight = State()

class Checkout(StatesGroup):
    waiting_name     = State()
    waiting_username = State()  # Telegram @username
    waiting_phone    = State()
    waiting_address  = State()
    waiting_confirm  = State()

class Review(StatesGroup):
    waiting_comment = State()  # waiting_rating removed: rating is passed via callback, not separate state

class AdminAddProduct(StatesGroup):
    waiting_name     = State()
    waiting_price    = State()
    waiting_category = State()
    waiting_gender   = State()
    waiting_desc     = State()
    waiting_photo    = State()

class AdminEditProduct(StatesGroup):
    select_product = State()
    waiting_name   = State()
    waiting_price  = State()
    waiting_desc   = State()
    waiting_photo  = State()

class AdminSendQC(StatesGroup):
    waiting_order_id = State()
    waiting_photo    = State()
class AdminPriceAdjust(StatesGroup):
    waiting_price  = State()
    waiting_reason = State()
