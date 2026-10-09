@echo off
chcp 65001 >nul
cd /d %~dp0

if not exist venv (
    echo [AtirMagaz] Virtual muhit yaratilmoqda...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

python manage.py migrate
python manage.py seed_atir
start "" http://127.0.0.1:8000/
python manage.py runserver 127.0.0.1:8000
pause
