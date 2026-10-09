from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        label="Baho", coerce=int, choices=[(i, i) for i in range(5, 0, -1)],
        widget=forms.RadioSelect, initial=5)

    class Meta:
        model = Review
        fields = ["name", "rating", "text"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ismingiz"}),
            "text": forms.Textarea(attrs={"rows": 4, "placeholder": "Hid sizga qanday tuyuldi? Qancha saqlanadi?"}),
        }
