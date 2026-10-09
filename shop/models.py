from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count, Min, Q
from django.urls import reverse


class Brand(models.Model):
    name = models.CharField("Nomi", max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    country = models.CharField("Mamlakat", max_length=60, blank=True)
    founded = models.PositiveIntegerField("Tashkil topgan yil", null=True, blank=True)
    description = models.TextField("Tavsif", blank=True)
    is_niche = models.BooleanField("Nish brend", default=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "Brend"
        verbose_name_plural = "Brendlar"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("shop:brand", args=[self.slug])


class Note(models.Model):
    name = models.CharField("Nota", max_length=60, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Nota"
        verbose_name_plural = "Notalar"

    def __str__(self):
        return self.name


class PerfumeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def with_stats(self):
        """Katalog kartochkasi uchun kerakli hisob-kitoblar bitta so'rovda."""
        full_size = Q(variants__is_sample=False)
        return self.annotate(
            price_from=Min("variants__price", filter=full_size),
            old_price_from=Min("variants__old_price", filter=full_size),
            rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
            reviews_total=Count("reviews", filter=Q(reviews__is_approved=True), distinct=True),
        ).select_related("brand")


class Perfume(models.Model):
    class Gender(models.TextChoices):
        WOMEN = "women", "Ayollar uchun"
        MEN = "men", "Erkaklar uchun"
        UNISEX = "unisex", "Uniseks"

    class Concentration(models.TextChoices):
        PARFUM = "parfum", "Parfum"
        EDP = "edp", "Eau de Parfum"
        EDT = "edt", "Eau de Toilette"
        EDC = "edc", "Eau de Cologne"

    class Family(models.TextChoices):
        FLORAL = "floral", "Gulli"
        ORIENTAL = "oriental", "Sharqona"
        WOODY = "woody", "Yog'ochli"
        CITRUS = "citrus", "Sitrusli"
        FOUGERE = "fougere", "Fujer"
        GOURMAND = "gourmand", "Gurmand"
        CHYPRE = "chypre", "Shipr"
        AQUATIC = "aquatic", "Dengiz (suvli)"
        LEATHER = "leather", "Teri"

    class Season(models.TextChoices):
        ALL = "all", "Har qanday fasl"
        WARM = "warm", "Bahor — yoz"
        COLD = "cold", "Kuz — qish"

    class TimeOfDay(models.TextChoices):
        ANY = "any", "Kun va kechqurun"
        DAY = "day", "Kunduzi"
        EVENING = "evening", "Kechqurun"

    class Shape(models.TextChoices):
        CLASSIC = "classic", "Klassik"
        ROUND = "round", "Dumaloq"
        TALL = "tall", "Baland"
        SQUARE = "square", "Kvadrat"
        FACET = "facet", "Qirrali"

    class Cap(models.TextChoices):
        GOLD = "gold", "Oltin"
        BLACK = "black", "Qora"
        SILVER = "silver", "Kumush"

    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="perfumes", verbose_name="Brend")
    name = models.CharField("Nomi", max_length=120)
    slug = models.SlugField(unique=True, max_length=160)
    gender = models.CharField("Kim uchun", max_length=10, choices=Gender.choices)
    concentration = models.CharField("Konsentratsiya", max_length=10, choices=Concentration.choices)
    family = models.CharField("Hid oilasi", max_length=12, choices=Family.choices)
    year = models.PositiveIntegerField("Chiqarilgan yil", null=True, blank=True)
    perfumer = models.CharField("Parfyumer", max_length=120, blank=True)
    description = models.TextField("Tavsif")

    top_notes = models.ManyToManyField(Note, related_name="as_top", blank=True, verbose_name="Yuqori notalar")
    heart_notes = models.ManyToManyField(Note, related_name="as_heart", blank=True, verbose_name="Yurak notalari")
    base_notes = models.ManyToManyField(Note, related_name="as_base", blank=True, verbose_name="Asos notalari")

    season = models.CharField("Fasl", max_length=10, choices=Season.choices, default=Season.ALL)
    time_of_day = models.CharField("Vaqt", max_length=10, choices=TimeOfDay.choices, default=TimeOfDay.ANY)
    longevity = models.PositiveSmallIntegerField(
        "Turg'unlik (1-5)", default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    sillage = models.PositiveSmallIntegerField(
        "Shleyf (1-5)", default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])

    image = models.ImageField("Rasm", upload_to="perfumes/", blank=True,
                              help_text="Bo'sh qolsa, flakon rasmi avtomatik chiziladi.")
    color = models.CharField("Suyuqlik rangi", max_length=7, default="#D9A441",
                             help_text="HEX, masalan #D9A441 — avtomatik flakon rasmi uchun.")
    shape = models.CharField("Flakon shakli", max_length=10, choices=Shape.choices, default=Shape.CLASSIC)
    cap = models.CharField("Qopqoq", max_length=10, choices=Cap.choices, default=Cap.GOLD)

    is_new = models.BooleanField("Yangi", default=False)
    is_bestseller = models.BooleanField("Xit", default=False)
    is_active = models.BooleanField("Saytda ko'rinadi", default=True)
    sold_count = models.PositiveIntegerField("Sotilgan", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PerfumeQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Atir"
        verbose_name_plural = "Atirlar"

    def __str__(self):
        return f"{self.brand.name} {self.name}"

    def get_absolute_url(self):
        return reverse("shop:perfume", args=[self.slug])

    @property
    def full_name(self):
        return str(self)

    def default_variant(self):
        """Kartochkadagi «Savatga» tugmasi qo'shadigan hajm: mavjud eng kichik flakon."""
        variants = [v for v in self.variants.all() if not v.is_sample]
        in_stock = [v for v in variants if v.stock > 0]
        pool = in_stock or variants
        return min(pool, key=lambda v: v.volume_ml) if pool else None

    def in_stock(self):
        return any(v.stock > 0 for v in self.variants.all())

    def discount_percent(self):
        price = getattr(self, "price_from", None)
        old = getattr(self, "old_price_from", None)
        if price and old and old > price:
            return round((old - price) * 100 / old)
        return 0


class Variant(models.Model):
    perfume = models.ForeignKey(Perfume, on_delete=models.CASCADE, related_name="variants")
    volume_ml = models.PositiveIntegerField("Hajm, ml")
    price = models.PositiveIntegerField("Narx, so'm")
    old_price = models.PositiveIntegerField("Eski narx, so'm", null=True, blank=True,
                                            help_text="To'ldirilsa, chegirma ko'rsatiladi.")
    stock = models.PositiveIntegerField("Omborda, dona", default=10)
    is_sample = models.BooleanField("Probnik (atomayzer)", default=False)

    class Meta:
        ordering = ["volume_ml"]
        unique_together = [("perfume", "volume_ml")]
        verbose_name = "Hajm va narx"
        verbose_name_plural = "Hajmlar va narxlar"

    def __str__(self):
        return f"{self.perfume} — {self.label}"

    @property
    def label(self):
        return f"{self.volume_ml} ml probnik" if self.is_sample else f"{self.volume_ml} ml"

    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return round((self.old_price - self.price) * 100 / self.old_price)
        return 0


class Review(models.Model):
    perfume = models.ForeignKey(Perfume, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("Ism", max_length=80)
    rating = models.PositiveSmallIntegerField(
        "Baho", validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField("Sharh")
    is_approved = models.BooleanField("Tasdiqlangan", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"

    def __str__(self):
        return f"{self.name} → {self.perfume} ({self.rating}★)"
