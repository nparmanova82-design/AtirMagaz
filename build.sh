#!/usr/bin/env bash
# Render har deployda shu skriptni ishga tushiradi
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py seed_atir      # katalog bo'sh bo'lsagina to'ldiradi
python manage.py ensure_admin   # DJANGO_SUPERUSER_PASSWORD bo'yicha admin
