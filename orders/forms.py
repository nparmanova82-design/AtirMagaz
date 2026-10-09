import re

from django import forms

from .models import Order


def normalize_phone(raw):
    """«90 123-45-67», «+998901234567» → «+998901234567». Noto'g'ri bo'lsa None."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 9:
        digits = "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return "+" + digits
    return None


class PhoneField(forms.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("label", "Telefon raqam")
        kwargs.setdefault("widget", forms.TextInput(attrs={
            "placeholder": "+998 90 123 45 67", "inputmode": "tel", "autocomplete": "tel"}))
        super().__init__(**kwargs)

    def clean(self, value):
        value = super().clean(value)
        if not value:
            return value
        phone = normalize_phone(value)
        if not phone:
            raise forms.ValidationError("Telefon raqamini +998 XX XXX XX XX ko'rinishida kiriting.")
        return phone


class CheckoutForm(forms.ModelForm):
    phone = PhoneField()

    class Meta:
        model = Order
        fields = ["full_name", "phone", "email", "delivery", "region", "address",
                  "payment", "gift_wrap", "gift_note", "comment"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Ism va familiya", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Chek yuborish uchun (ixtiyoriy)"}),
            "delivery": forms.RadioSelect,
            "payment": forms.RadioSelect,
            "address": forms.TextInput(attrs={"placeholder": "Tuman, ko'cha, uy, xonadon, mo'ljal"}),
            "gift_note": forms.TextInput(attrs={"placeholder": "Masalan: Tug'ilgan kuning bilan, onajon!"}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Kuryer uchun izoh, qulay vaqt..."}),
        }

    def clean(self):
        data = super().clean()
        if data.get("delivery") != Order.Delivery.PICKUP and not data.get("address"):
            self.add_error("address", "Yetkazib berish uchun manzilni kiriting.")
        if data.get("delivery") == Order.Delivery.POST and data.get("region") == "tashkent":
            self.add_error("delivery", "Toshkent bo'ylab kuryer yoki olib ketishni tanlang.")
        return data


class TrackForm(forms.Form):
    number = forms.CharField(label="Buyurtma raqami", widget=forms.TextInput(attrs={"placeholder": "AM-123456"}))
    phone = PhoneField()

    def clean_number(self):
        value = self.cleaned_data["number"].strip().upper().replace(" ", "")
        if value.isdigit():
            value = f"AM-{value}"
        return value
