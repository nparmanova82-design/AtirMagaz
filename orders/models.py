import secrets

from django.conf import settings
from django.db import models

from shop.models import Variant


class PromoCode(models.Model):
    code = models.CharField("Kod", max_length=30, unique=True)
    percent = models.PositiveSmallIntegerField("Chegirma, %")
    min_total = models.PositiveIntegerField("Minimal summa, so'm", default=0)
    is_active = models.BooleanField("Faol", default=True)
    description = models.CharField("Izoh", max_length=150, blank=True)

    class Meta:
        verbose_name = "Promokod"
        verbose_name_plural = "Promokodlar"

    def __str__(self):
        return f"{self.code} (−{self.percent}%)"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        CONFIRMED = "confirmed", "Tasdiqlandi"
        SHIPPING = "shipping", "Yo'lda"
        DELIVERED = "delivered", "Yetkazildi"
        CANCELLED = "cancelled", "Bekor qilindi"

    class Delivery(models.TextChoices):
        COURIER = "courier", "Kuryer orqali"
        PICKUP = "pickup", "Do'kondan olib ketish"
        POST = "post", "Viloyatlarga pochta (BTS / Uzpost)"

    class Payment(models.TextChoices):
        CASH = "cash", "Naqd pul (qabul qilganda)"
        CARD = "card", "Karta orqali (qabul qilganda)"
        CLICK = "click", "Click"
        PAYME = "payme", "Payme"
        UZUM = "uzum", "Uzum Bank"

    REGIONS = [
        ("tashkent", "Toshkent shahri"),
        ("tashkent_reg", "Toshkent viloyati"),
        ("andijan", "Andijon"),
        ("bukhara", "Buxoro"),
        ("fergana", "Farg'ona"),
        ("jizzakh", "Jizzax"),
        ("kashkadarya", "Qashqadaryo"),
        ("khorezm", "Xorazm"),
        ("namangan", "Namangan"),
        ("navoi", "Navoiy"),
        ("samarkand", "Samarqand"),
        ("surkhandarya", "Surxondaryo"),
        ("syrdarya", "Sirdaryo"),
        ("karakalpakstan", "Qoraqalpog'iston"),
    ]

    number = models.CharField("Raqam", max_length=12, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name="orders", verbose_name="Mijoz")
    full_name = models.CharField("F.I.Sh.", max_length=120)
    phone = models.CharField("Telefon", max_length=20)
    email = models.EmailField("Email", blank=True)
    region = models.CharField("Viloyat", max_length=20, choices=REGIONS, default="tashkent")
    address = models.CharField("Manzil", max_length=255, blank=True)
    delivery = models.CharField("Yetkazib berish", max_length=10, choices=Delivery.choices,
                                default=Delivery.COURIER)
    payment = models.CharField("To'lov", max_length=10, choices=Payment.choices, default=Payment.CASH)
    comment = models.TextField("Izoh", blank=True)
    gift_wrap = models.BooleanField("Sovg'a qadog'i", default=False)
    gift_note = models.CharField("Otkritka matni", max_length=200, blank=True)

    promo_code = models.CharField("Promokod", max_length=30, blank=True)
    subtotal = models.PositiveIntegerField("Mahsulotlar", default=0)
    discount = models.PositiveIntegerField("Chegirma", default=0)
    delivery_cost = models.PositiveIntegerField("Yetkazib berish narxi", default=0)
    gift_wrap_cost = models.PositiveIntegerField("Qadoq narxi", default=0)
    total = models.PositiveIntegerField("Jami", default=0)

    status = models.CharField("Holat", max_length=12, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"

    def __str__(self):
        return f"#{self.number}"

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._new_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _new_number():
        while True:
            number = f"AM-{secrets.randbelow(900000) + 100000}"
            if not Order.objects.filter(number=number).exists():
                return number

    # Holat shkalasi uchun: bekor qilinmagan buyurtma qaysi bosqichda
    STEPS = [Status.NEW, Status.CONFIRMED, Status.SHIPPING, Status.DELIVERED]

    def steps(self):
        if self.status == self.Status.CANCELLED:
            return []
        current = self.STEPS.index(self.status)
        return [
            {"label": self.Status(s).label, "done": i <= current, "current": i == current}
            for i, s in enumerate(self.STEPS)
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    # Buyurtma paytidagi nom va narx — keyin katalog o'zgarsa ham tarix buzilmaydi.
    title = models.CharField("Mahsulot", max_length=200)
    volume_label = models.CharField("Hajm", max_length=30)
    price = models.PositiveIntegerField("Narx")
    quantity = models.PositiveIntegerField("Soni", default=1)

    class Meta:
        verbose_name = "Buyurtma qatori"
        verbose_name_plural = "Buyurtma qatorlari"

    def __str__(self):
        return f"{self.title} {self.volume_label} × {self.quantity}"

    @property
    def line_total(self):
        return self.price * self.quantity
