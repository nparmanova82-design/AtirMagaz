from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from orders.forms import normalize_phone

User = get_user_model()


def _clean_phone(value):
    phone = normalize_phone(value)
    if not phone:
        raise forms.ValidationError("Telefon raqamini +998 XX XXX XX XX ko'rinishida kiriting.")
    return phone


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Ismingiz", max_length=60,
                                 widget=forms.TextInput(attrs={"autocomplete": "given-name"}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["first_name", "username", "email"]
        labels = {"username": "Telefon raqam", "email": "Email (ixtiyoriy)"}
        help_texts = {"username": ""}
        widgets = {"username": forms.TextInput(attrs={
            "placeholder": "+998 90 123 45 67", "inputmode": "tel", "autocomplete": "tel"})}

    def clean_username(self):
        phone = _clean_phone(self.cleaned_data["username"])
        if User.objects.filter(username=phone).exists():
            raise forms.ValidationError("Bu raqam bilan hisob allaqachon mavjud. Kirish sahifasiga o'ting.")
        return phone


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Telefon raqam", widget=forms.TextInput(attrs={
        "placeholder": "+998 90 123 45 67", "inputmode": "tel", "autofocus": True}))

    def clean_username(self):
        value = self.cleaned_data["username"]
        # «admin» kabi oddiy loginlar ham ishlashi uchun telefon bo'lmasa o'zgartirmaymiz
        return normalize_phone(value) or value


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {"first_name": "Ism", "last_name": "Familiya", "email": "Email"}
