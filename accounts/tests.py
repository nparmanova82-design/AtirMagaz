from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pages.models import ContactMessage, Subscriber


class AccountTests(TestCase):
    def test_register_with_phone_then_login(self):
        r = self.client.post(reverse("accounts:register"), {
            "first_name": "Madina", "username": "93 555 66 77", "email": "",
            "password1": "atir-parol-77", "password2": "atir-parol-77"})
        self.assertRedirects(r, reverse("accounts:profile"))
        user = get_user_model().objects.get()
        self.assertEqual(user.username, "+998935556677")

        self.client.post(reverse("accounts:logout"))
        r = self.client.post(reverse("accounts:login"), {"username": "+998 93 555 66 77", "password": "atir-parol-77"})
        self.assertRedirects(r, reverse("accounts:profile"))

    def test_bad_phone_rejected(self):
        r = self.client.post(reverse("accounts:register"), {
            "first_name": "X", "username": "12345", "password1": "atir-parol-77", "password2": "atir-parol-77"})
        self.assertIn("username", r.context["form"].errors)

    def test_profile_requires_login(self):
        r = self.client.get(reverse("accounts:profile"))
        self.assertEqual(r.status_code, 302)


class PagesFormsTests(TestCase):
    def test_contact_form_saves_message(self):
        r = self.client.post(reverse("pages:contacts"), {
            "name": "Jasur", "phone": "+998901112233", "topic": "consult", "message": "Kechki atir kerak"})
        self.assertRedirects(r, reverse("pages:contacts"))
        self.assertEqual(ContactMessage.objects.get().topic, "consult")

    def test_subscribe(self):
        self.client.post(reverse("pages:subscribe"), {"email": "Test@Mail.uz"})
        self.client.post(reverse("pages:subscribe"), {"email": "test@mail.uz"})
        self.assertEqual(Subscriber.objects.count(), 1)
