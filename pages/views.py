from django import forms
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from orders.forms import PhoneField
from shop.models import Brand, Perfume
from shop.views import FAMILY_INFO

from .models import ContactMessage, Subscriber


class ContactForm(forms.ModelForm):
    phone = PhoneField()

    class Meta:
        model = ContactMessage
        fields = ["name", "phone", "email", "topic", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ismingiz"}),
            "email": forms.EmailInput(attrs={"placeholder": "Ixtiyoriy"}),
            "message": forms.Textarea(attrs={"rows": 5, "placeholder": "Savolingiz yoki xabaringiz"}),
        }


STORES = [
    {"name": "AtirMagaz — Amir Temur", "address": "Toshkent, Amir Temur ko'chasi, 15",
     "landmark": "Amir Temur xiyoboni metro bekati yonida", "hours": "Har kuni 10:00 — 22:00",
     "phone": "+998 71 200 45 45"},
    {"name": "AtirMagaz — Samarqand Darvoza", "address": "Toshkent, Qoratosh ko'chasi, 5A, 1-qavat",
     "landmark": "Samarqand Darvoza savdo markazi", "hours": "Har kuni 10:00 — 22:00",
     "phone": "+998 71 200 45 46"},
    {"name": "AtirMagaz — Samarqand", "address": "Samarqand, Registon ko'chasi, 40",
     "landmark": "Registon maydoniga 5 daqiqa", "hours": "Har kuni 10:00 — 21:00",
     "phone": "+998 66 233 45 45"},
]

FAQ = [
    ("Mahsulotlar 100% originalmi?", [
        "Ha. Biz atirlarni faqat rasmiy distribyutorlar va brendlarning vakolatli yetkazib "
        "beruvchilaridan olamiz. Har bir partiya sertifikat va bojxona hujjatlariga ega.",
        "Agar mahsulot originalligiga shubha qilsangiz — hujjatlarni do'konda ko'rsatamiz "
        "va pulingizni to'liq qaytarishga kafolat beramiz.",
    ]),
    ("Probnik (atomayzer) nima?", [
        "Bu original flakondan steril 5 ml atomayzerga quyilgan atir. Katta flakon olishdan oldin "
        "hidni terida bir necha kun sinab ko'rish uchun eng yaxshi usul.",
    ]),
    ("Yetkazib berish qancha vaqt oladi?", [
        "Toshkent bo'ylab — 1 kun ichida (14:00 gacha berilgan buyurtmalar shu kuni yetkaziladi). "
        "Viloyatlarga — 2 — 4 ish kuni.",
    ]),
    ("Yetkazib berish narxi qancha?", [
        "500 000 so'mdan yuqori buyurtmalar butun O'zbekiston bo'ylab bepul yetkaziladi. "
        "Undan kam bo'lsa: Toshkent — 25 000 so'm, viloyatlar — 45 000 so'm. Do'kondan olib ketish — bepul.",
    ]),
    ("Qanday to'lash mumkin?", [
        "Naqd pul yoki karta orqali qabul qilganda, shuningdek Click, Payme va Uzum Bank orqali onlayn.",
    ]),
    ("Atirni qaytarish mumkinmi?", [
        "Ochilmagan, plyonkasi buzilmagan atirni 14 kun ichida qaytarish yoki almashtirish mumkin. "
        "Ochilgan atirlar sanitariya qoidalariga ko'ra qaytarilmaydi — shuning uchun avval probnik olishni tavsiya qilamiz.",
    ]),
    ("Sovg'a qadog'i bormi?", [
        "Ha, buyurtma rasmiylashtirishda «Sovg'a qadog'i» ni belgilang (30 000 so'm). Atir brendli qutiga "
        "joylanadi, lenta bog'lanadi va xohlasangiz otkritkaga tilagingizni yozib qo'yamiz.",
    ]),
    ("EDP, EDT va Parfum o'rtasidagi farq nima?", [
        "Farq — atir moylari konsentratsiyasida. Parfum (20—30%) eng to'yingan va uzoq saqlanadi; "
        "Eau de Parfum (15—20%) — 6—8 soat; Eau de Toilette (8—15%) — 3—5 soat, yengilroq; "
        "Eau de Cologne (2—5%) — eng yengil, 2 soatgacha.",
    ]),
    ("Atirni qanday to'g'ri saqlash kerak?", [
        "Quyosh nuri tushmaydigan, salqin joyda va qutisida saqlang. Hammomda saqlamang — harorat va namlik "
        "o'zgarishi hidni buzadi.",
    ]),
    ("Ulgurji yoki korporativ sovg'alar bormi?", [
        "Ha, korporativ mijozlar uchun maxsus narxlar va sovg'a to'plamlari mavjud. "
        "Aloqa sahifasidagi formada «Ulgurji / hamkorlik» mavzusini tanlang.",
    ]),
]


def about(request):
    bottles, shapes = [], set()
    for p in Perfume.objects.active().select_related("brand").filter(brand__is_niche=True).order_by("-sold_count"):
        if p.shape not in shapes:
            bottles.append(p)
            shapes.add(p.shape)
    return render(request, "pages/about.html", {
        "hero_bottles": bottles[:3],
        "stores": STORES,
        "perfume_count": Perfume.objects.active().count(),
        "brand_count": Brand.objects.count(),
    })


def contacts(request):
    topic = request.GET.get("mavzu")
    form = ContactForm(request.POST or None,
                       initial={"topic": topic if topic in ContactMessage.Topic.values else None})
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Xabaringiz yuborildi! Operatorimiz tez orada bog'lanadi.")
        return redirect("pages:contacts")
    return render(request, "pages/contacts.html", {"form": form, "stores": STORES})


def delivery(request):
    return render(request, "pages/delivery.html")


def faq(request):
    return render(request, "pages/faq.html", {"faq": FAQ})


def returns(request):
    return render(request, "pages/returns.html")


def guide(request):
    counts = {f["family"]: f["n"] for f in Perfume.objects.active().values("family").annotate(n=Count("id"))}
    families = [
        {"key": key, "label": label, "text": FAMILY_INFO[key][0], "color": FAMILY_INFO[key][1],
         "count": counts.get(key, 0)}
        for key, label in Perfume.Family.choices
    ]
    return render(request, "pages/guide.html", {"families": families})


@require_POST
def subscribe(request):
    email = request.POST.get("email", "").strip().lower()
    try:
        forms.EmailField().clean(email)
    except forms.ValidationError:
        messages.error(request, "Email manzilini to'g'ri kiriting.")
    else:
        _, created = Subscriber.objects.get_or_create(email=email)
        messages.success(request, "Obuna bo'ldingiz! Yangiliklar va yopiq aksiyalar endi pochtangizda."
                         if created else "Siz allaqachon obuna bo'lgansiz.")
    return redirect(request.POST.get("next") or "shop:home")


def not_found(request, exception):
    return render(request, "pages/404.html", status=404)
