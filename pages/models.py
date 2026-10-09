from django.db import models


class ContactMessage(models.Model):
    class Topic(models.TextChoices):
        QUESTION = "question", "Savol"
        ORDER = "order", "Buyurtma bo'yicha"
        CONSULT = "consult", "Atir tanlashda maslahat"
        WHOLESALE = "wholesale", "Ulgurji / hamkorlik"
        COMPLAINT = "complaint", "Shikoyat yoki taklif"

    name = models.CharField("Ism", max_length=80)
    phone = models.CharField("Telefon", max_length=20)
    email = models.EmailField("Email", blank=True)
    topic = models.CharField("Mavzu", max_length=12, choices=Topic.choices, default=Topic.QUESTION)
    message = models.TextField("Xabar")
    is_processed = models.BooleanField("Ko'rib chiqildi", default=False)
    created_at = models.DateTimeField("Yuborilgan", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Murojaat"
        verbose_name_plural = "Murojaatlar"

    def __str__(self):
        return f"{self.name} — {self.get_topic_display()}"


class Subscriber(models.Model):
    email = models.EmailField("Email", unique=True)
    created_at = models.DateTimeField("Obuna bo'lgan", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Obunachi"
        verbose_name_plural = "Obunachilar"

    def __str__(self):
        return self.email
