# AtirMagaz — original atirlar internet-do'koni

Django'da yozilgan parfyumeriya do'koni: katalog va filtrlar, hid piramidasi, probniklar,
savatcha va buyurtma rasmiylashtirish, «Atir tanlash» testi, shaxsiy kabinet va boshqaruv paneli.

## Ishga tushirish

Eng oson yo'li — `start_server.bat` faylini ikki marta bosing. U virtual muhit yaratadi,
kutubxonalarni o'rnatadi, bazani tayyorlaydi, demo katalogni yuklaydi va saytni brauzerda ochadi.

Qo'lda:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_atir          # 39 ta atir, 21 brend, sharhlar, promokodlar, admin
python manage.py runserver
```

Sayt: http://127.0.0.1:8000/ · Admin panel: http://127.0.0.1:8000/admin/

| Kim | Login | Parol |
|---|---|---|
| Administrator (faqat lokal) | `admin` | `admin12345` |

Demo promokodlar: **ATIR10** (−10%), **KUZ20** (−20%, 1,5 mln so'mdan).

Katalogni qayta yaratish: `python manage.py seed_atir --reset`.
Testlar: `python manage.py test`.

## Saytda nimalar bor

**Xarid qilish**
- Katalog: jins, brend, hid oilasi, konsentratsiya, narx oralig'i, chegirma, yangi, nish, mavjudlik bo'yicha filtrlar; 5 xil saralash; faol filtr «chip»lari
- Jonli qidiruv (atir nomi, brend va nota bo'yicha), tez qidiruv uchun `/` tugmasi
- Atir sahifasi: hajm tanlash (30/50/100 ml va 5 ml probnik), narx va qoldiq jonli yangilanadi, hid piramidasi (yuqori/yurak/asos notalar), turg'unlik va shleyf shkalasi, xususiyatlar, sharhlar va baho taqsimoti, o'xshash va yaqinda ko'rilgan atirlar
- Savatcha: son o'zgartirish, promokod, bepul yetkazib berishgacha qolgan summa
- Rasmiylashtirish: kuryer / olib ketish / pochta, 14 viloyat, naqd / karta / Click / Payme / Uzum, sovg'a qadog'i va otkritka matni; narx jonli hisoblanadi; ombor qoldig'i tekshiriladi
- Buyurtma holatini raqam va telefon orqali kuzatish
- Sevimlilar (ro'yxatdan o'tmasdan ham ishlaydi)
- «Atir tanlash» testi — 4 savol, mos kelish foizi bilan natijalar

**Sahifalar**: Biz haqimizda (hikoya, raqamlar, qadriyatlar, yo'l xaritasi, jamoa, butiklar),
Aloqa (forma + xarita), Yetkazib berish va to'lov, Savol-javoblar, Qaytarish, Atir qo'llanmasi, 404.

**Hisob**: telefon raqam orqali ro'yxatdan o'tish va kirish, buyurtmalar tarixi, ma'lumotlarni tahrirlash.

**Admin panel**: atirlar (hajm va narxlar shu yerning o'zida), brendlar, notalar, sharhlarni moderatsiya,
buyurtmalar va ularning holati, promokodlar, murojaatlar, obunachilar.

## Atir rasmlari

Atirga rasm yuklanmagan bo'lsa, sayt flakonni o'zi chizadi (SVG): suyuqlik rangi, flakon shakli
va qopqoq rangi admin paneldagi «Ko'rinish» bo'limida tanlanadi. Haqiqiy rasm yuklansa —
o'sha rasm ko'rsatiladi.

## Nimani almashtirish kerak

Do'kon nomi, telefon, manzil, ijtimoiy tarmoqlar va yetkazib berish narxlari —
`config/settings.py` dagi `SHOP` lug'atida. Butiklar ro'yxati va savol-javoblar — `pages/views.py`.
«Biz haqimizda» sahifasidagi hikoya, jamoa va raqamlar — `templates/pages/about.html`
(hozir namunaviy matn turibdi).

## Render'ga joylash

Loyihada tayyor Blueprint bor (`render.yaml`): veb-sayt + PostgreSQL baza, ikkalasi ham bepul tarifda,
Frankfurt serverida.

1. Quyidagi havolani oching va Render hisobingizga kiring (GitHub orqali kirish mumkin):
   https://render.com/deploy?repo=https://github.com/nparmanova82-design/AtirMagaz
2. **DJANGO_SUPERUSER_PASSWORD** maydoniga admin panel uchun parol yozing.
3. **Deploy Blueprint** tugmasini bosing. 5–10 daqiqadan keyin sayt
   `https://atirmagaz.onrender.com` (yoki Render ko'rsatgan manzil)da ochiladi.

Har deployda `build.sh` ishlaydi: kutubxonalar, statik fayllar, migratsiya, demo katalog
(faqat baza bo'sh bo'lsa) va admin (`admin` + siz kiritgan parol). GitHub'ga yangi commit
yuborilsa, Render saytni avtomatik yangilaydi.

**Bepul tarif cheklovlari:**
- 15 daqiqa hech kim kirmasa, sayt «uxlaydi» — keyingi birinchi ochilish ~1 daqiqa kutadi.
- Bepul PostgreSQL 30 kundan keyin to'xtaydi; ma'lumotlar o'chmasligi uchun undan keyin 14 kun
  ichida bazani pullik tarifga o'tkazish kerak.
- Admin orqali yuklangan rasmlar qayta deploy yoki uyquda o'chib ketadi (sayt o'rniga SVG flakonni
  ko'rsatadi). Doimiy rasmlar uchun pullik tarifdagi disk yoki bulutli xotira kerak.

Lokal `admin12345` paroli faqat kompyuteringizda (DEBUG rejimida) yaratiladi, serverda emas.

## Tuzilma

```
config/      sozlamalar, asosiy marshrutlar
build.sh     Render build skripti;  render.yaml — Render Blueprint
shop/        brendlar, notalar, atirlar, hajmlar, sharhlar, katalog, test, SVG flakon (templatetags)
orders/      savatcha (sessiyada), promokodlar, buyurtmalar, rasmiylashtirish, kuzatish
pages/       statik sahifalar, aloqa formasi, obuna
accounts/    ro'yxatdan o'tish, kirish, shaxsiy kabinet
templates/   shablonlar
static/      style.css (dizayn tizimi), main.js (kutubxonasiz interaktivlik)
```
