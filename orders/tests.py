from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from shop.models import Perfume, Variant

from .cart import quote
from .models import Order, PromoCode


class CheckoutFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_atir", verbosity=0)

    def _variant(self, min_price=0, **filters):
        return (Variant.objects.filter(is_sample=False, stock__gte=3, price__gte=min_price, **filters)
                .select_related("perfume").order_by("price").first())

    def _checkout_data(self, **extra):
        data = {
            "full_name": "Aziza Karimova", "phone": "90 123 45 67", "email": "",
            "delivery": "courier", "region": "tashkent", "address": "Chilonzor 5, 12-uy",
            "payment": "cash", "gift_note": "", "comment": "",
        }
        data.update(extra)
        return data

    def test_add_to_cart_ajax_returns_count(self):
        v = self._variant()
        r = self.client.post(reverse("orders:cart_add"), {"variant": v.pk, "quantity": 2},
                             HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r.json()["count"], 2)
        self.assertTrue(r.json()["ok"])

    def test_cart_never_exceeds_stock(self):
        v = self._variant()
        self.client.post(reverse("orders:cart_add"), {"variant": v.pk, "quantity": v.stock + 50})
        self.assertEqual(self.client.session["cart"][str(v.pk)], v.stock)

    def test_full_checkout_creates_order_and_reduces_stock(self):
        v = self._variant(min_price=600_000)
        stock_before, sold_before = v.stock, v.perfume.sold_count
        self.client.post(reverse("orders:cart_add"), {"variant": v.pk, "quantity": 2})

        r = self.client.post(reverse("orders:checkout"), self._checkout_data(gift_wrap="on", gift_note="Tabriklayman!"))
        order = Order.objects.get()
        self.assertRedirects(r, reverse("orders:success", args=[order.number]))

        self.assertEqual(order.phone, "+998901234567")
        self.assertEqual(order.subtotal, v.price * 2)
        self.assertEqual(order.delivery_cost, 0)  # 500 000 so'mdan oshdi — bepul
        self.assertEqual(order.gift_wrap_cost, 30_000)
        self.assertEqual(order.total, v.price * 2 + 30_000)
        self.assertEqual(order.items.get().quantity, 2)

        v.refresh_from_db()
        self.assertEqual(v.stock, stock_before - 2)
        self.assertEqual(Perfume.objects.get(pk=v.perfume_id).sold_count, sold_before + 2)
        self.assertNotIn(str(v.pk), self.client.session.get("cart", {}))

        # Muvaffaqiyat sahifasi faqat buyurtma egasiga ochiladi
        self.assertEqual(self.client.get(reverse("orders:success", args=[order.number])).status_code, 200)
        from django.test import Client
        self.assertEqual(Client().get(reverse("orders:success", args=[order.number])).status_code, 404)

    def test_checkout_rejects_when_stock_ran_out(self):
        v = self._variant()
        self.client.post(reverse("orders:cart_add"), {"variant": v.pk, "quantity": 3})
        Variant.objects.filter(pk=v.pk).update(stock=1)  # boshqa mijoz sotib oldi
        r = self.client.post(reverse("orders:checkout"), self._checkout_data())
        self.assertRedirects(r, reverse("orders:cart"))
        self.assertFalse(Order.objects.exists())
        self.assertEqual(self.client.session["cart"][str(v.pk)], 1)

    def test_address_required_for_courier_but_not_pickup(self):
        v = self._variant()
        self.client.post(reverse("orders:cart_add"), {"variant": v.pk})
        r = self.client.post(reverse("orders:checkout"), self._checkout_data(address=""))
        self.assertEqual(r.status_code, 200)
        self.assertIn("address", r.context["form"].errors)
        r = self.client.post(reverse("orders:checkout"), self._checkout_data(address="", delivery="pickup"))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Order.objects.get().delivery_cost, 0)

    def test_promo_code_applies_discount(self):
        v = self._variant(min_price=1_600_000)
        self.client.post(reverse("orders:cart_add"), {"variant": v.pk})
        self.client.post(reverse("orders:promo_apply"), {"code": "kuz20"})
        self.client.post(reverse("orders:checkout"), self._checkout_data())
        order = Order.objects.get()
        self.assertEqual(order.promo_code, "KUZ20")
        self.assertEqual(order.discount, v.price * 20 // 100)

    def test_unknown_promo_is_rejected(self):
        self.client.post(reverse("orders:promo_apply"), {"code": "YOQ"})
        self.assertNotIn("promo_code", self.client.session)

    def test_track_order_by_number_and_phone(self):
        v = self._variant()
        self.client.post(reverse("orders:cart_add"), {"variant": v.pk})
        self.client.post(reverse("orders:checkout"), self._checkout_data())
        order = Order.objects.get()
        r = self.client.get(reverse("orders:track"), {"number": order.number, "phone": "+998 90 123 45 67"})
        self.assertEqual(r.context["order"], order)
        r = self.client.get(reverse("orders:track"), {"number": order.number, "phone": "+998 99 000 00 00"})
        self.assertIsNone(r.context["order"])


class QuoteTests(TestCase):
    def test_delivery_rules(self):
        self.assertEqual(quote(100_000)["delivery_cost"], 25_000)
        self.assertEqual(quote(100_000, region="samarkand")["delivery_cost"], 45_000)
        self.assertEqual(quote(100_000, delivery="pickup")["delivery_cost"], 0)
        self.assertEqual(quote(500_000)["delivery_cost"], 0)

    def test_promo_minimum_total(self):
        promo = PromoCode(code="X", percent=20, min_total=1_000_000)
        self.assertEqual(quote(900_000, promo)["discount"], 0)
        self.assertTrue(quote(900_000, promo)["promo_note"])
        self.assertEqual(quote(1_000_000, promo)["discount"], 200_000)
