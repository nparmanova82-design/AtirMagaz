"""Sessiyadagi savatcha va narx hisob-kitobi.

Savatcha sessiyada {variant_id: soni} ko'rinishida turadi; narxlar har safar bazadan olinadi,
shuning uchun admin narxni o'zgartirsa, savatchada ham darhol yangilanadi.
"""
from django.conf import settings

from shop.models import Variant

from .models import PromoCode

CART_KEY = "cart"
PROMO_KEY = "promo_code"


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = {str(k): int(v) for k, v in self.session.get(CART_KEY, {}).items()}
        self._lines = None

    def _save(self):
        self.session[CART_KEY] = self.data
        self._lines = None

    def __len__(self):
        return sum(self.data.values())

    def quantity_of(self, variant_id):
        return self.data.get(str(variant_id), 0)

    def add(self, variant, quantity=1, replace=False):
        """Soni ombordagi qoldiqdan oshmaydi. Haqiqiy qo'yilgan sonni qaytaradi."""
        key = str(variant.pk)
        new_qty = quantity if replace else self.data.get(key, 0) + quantity
        new_qty = max(0, min(new_qty, variant.stock))
        if new_qty:
            self.data[key] = new_qty
        else:
            self.data.pop(key, None)
        self._save()
        return new_qty

    def remove(self, variant_id):
        self.data.pop(str(variant_id), None)
        self._save()

    def clear(self):
        self.data = {}
        self._save()
        self.session.pop(PROMO_KEY, None)

    def lines(self):
        if self._lines is None:
            variants = (Variant.objects.filter(pk__in=self.data.keys(), perfume__is_active=True)
                        .select_related("perfume__brand"))
            by_id = {str(v.pk): v for v in variants}
            self._lines = []
            for key, qty in self.data.items():
                variant = by_id.get(key)
                if not variant:
                    continue
                self._lines.append({
                    "variant": variant,
                    "perfume": variant.perfume,
                    "quantity": qty,
                    "price": variant.price,
                    "total": variant.price * qty,
                    "over_stock": qty > variant.stock,
                })
        return self._lines

    @property
    def subtotal(self):
        return sum(line["total"] for line in self.lines())

    # — Promokod —
    def promo(self):
        code = self.session.get(PROMO_KEY)
        if not code:
            return None
        return PromoCode.objects.filter(code=code, is_active=True).first()

    def set_promo(self, code):
        self.session[PROMO_KEY] = code

    def drop_promo(self):
        self.session.pop(PROMO_KEY, None)


def quote(subtotal, promo=None, region="tashkent", delivery="courier", gift_wrap=False):
    """Buyurtma summasi. Savatcha, checkout va JS bir xil qoidalardan foydalanadi."""
    shop = settings.SHOP
    discount = 0
    promo_note = ""
    if promo:
        if subtotal >= promo.min_total:
            discount = subtotal * promo.percent // 100
        else:
            promo_note = f"{promo.code} kodi {promo.min_total:,} so'mdan boshlab ishlaydi".replace(",", " ")
    after_discount = subtotal - discount

    if delivery == "pickup" or subtotal == 0 or after_discount >= shop["free_delivery_from"]:
        delivery_cost = 0
    elif region == "tashkent":
        delivery_cost = shop["delivery_tashkent"]
    else:
        delivery_cost = shop["delivery_regions"]

    wrap_cost = shop["gift_wrap_price"] if gift_wrap else 0
    return {
        "subtotal": subtotal,
        "discount": discount,
        "promo_note": promo_note,
        "delivery_cost": delivery_cost,
        "gift_wrap_cost": wrap_cost,
        "total": after_discount + delivery_cost + wrap_cost,
        "free_left": max(0, shop["free_delivery_from"] - after_discount),
        "free_progress": min(100, round(after_discount * 100 / shop["free_delivery_from"])),
    }
