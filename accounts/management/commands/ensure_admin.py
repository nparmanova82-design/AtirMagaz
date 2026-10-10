"""Serverda administrator yaratadi: login va parol muhit o'zgaruvchilaridan olinadi.

    DJANGO_SUPERUSER_USERNAME (standart: admin)
    DJANGO_SUPERUSER_PASSWORD (majburiy — bo'lmasa hech narsa qilinmaydi)
    DJANGO_SUPERUSER_EMAIL    (ixtiyoriy)

Admin allaqachon bo'lsa, unga tegmaydi — admin paneldan o'zgartirilgan parol saqlanib qoladi.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "DJANGO_SUPERUSER_* muhit o'zgaruvchilari bo'yicha administrator yaratadi"

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME") or "admin"
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not password:
            self.stdout.write("DJANGO_SUPERUSER_PASSWORD berilmagan — admin yaratilmadi.")
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Admin «{username}» allaqachon mavjud.")
            return
        User.objects.create_superuser(username, os.environ.get("DJANGO_SUPERUSER_EMAIL", ""), password)
        self.stdout.write(self.style.SUCCESS(f"Admin «{username}» yaratildi."))
