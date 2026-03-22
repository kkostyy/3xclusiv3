# utils/utils.py
from config import SIZE_CHART, ADMIN_IDS, REFERRAL_TIERS, REFERRAL_MAX_DISCOUNT
from locales import gt

_carts: dict = {}

def get_cart(tid): return _carts.setdefault(tid, {})
def cart_empty(tid): return not bool(_carts.get(tid))
def clear_cart(tid): _carts[tid] = {}
def cart_total(tid): return sum(v["price"] * v["qty"] for v in get_cart(tid).values())

def add_to_cart(tid, pid, name, price, photo_id=None):
    c = get_cart(tid)
    if pid in c:
        c[pid]["qty"] += 1
    else:
        c[pid] = {"name": name, "price": price, "qty": 1, "photo_id": photo_id}

def cart_items(tid):
    return [{"pid": k, **v} for k, v in get_cart(tid).items()]

def format_cart(tid, lang):
    c = get_cart(tid)
    if not c: return gt("cart_empty", lang)
    text = gt("cart_header", lang)
    for v in c.values():
        text += f"  • {v['name']} × {v['qty']} = {v['price']*v['qty']:.2f} €\n"
    text += gt("cart_total", lang, total=f"{cart_total(tid):.2f}")
    return text

def recommend_size(h, w):
    for size, r in SIZE_CHART.items():
        if r["height"][0] <= h <= r["height"][1] and r["weight"][0] <= w <= r["weight"][1]:
            return size
    if h < 165: return "S"
    if h < 175: return "M"
    if h < 183: return "L"
    return "XL"

def is_admin(tid): return tid in ADMIN_IDS
def ref_link(username, tid): return f"https://t.me/{username}?start=ref_{tid}"

def build_receipt(oid, name, username, phone, address, items, total, lang, discount_pct=0, saved=0.0):
    lines = "\n".join(f"  • {i['name']} × {i['qty']} = {i['price']*i['qty']:.2f} €" for i in items)
    discount_line = ""
    if discount_pct > 0:
        labels = {"ru": f"🎁 Скидка {discount_pct}%: −{saved:.2f} €", "en": f"🎁 Discount {discount_pct}%: −{saved:.2f} €", "et": f"🎁 Allahindlus {discount_pct}%: −{saved:.2f} €"}
        discount_line = "\n" + labels.get(lang, labels["en"])
    return gt("receipt", lang, order_id=oid, name=name, username=username, phone=phone, address=address, items=lines, total=f"{total:.2f}") + discount_line


def get_referral_discount(ref_count: int) -> int:
    """Возвращает % скидки по количеству рефералов."""
    discount = 0
    for threshold, pct in REFERRAL_TIERS:
        if ref_count >= threshold:
            discount = pct
    return min(discount, REFERRAL_MAX_DISCOUNT)

def apply_discount(total: float, discount_pct: int) -> tuple[float, float]:
    """Возвращает (итого со скидкой, сумма скидки)."""
    if discount_pct <= 0:
        return total, 0.0
    saved = round(total * discount_pct / 100, 2)
    return round(total - saved, 2), saved
