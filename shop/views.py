from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Exists, F, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_POST

from .forms import ReviewForm
from .models import Brand, Note, Perfume, Review, Variant
from .session_lists import get_recent, get_wishlist, push_recent, toggle_wishlist
from .templatetags.shop_tags import som

PER_PAGE = 12

SORTS = {
    "popular": ("Ommabop", ["-sold_count"]),
    "new": ("Yangi kelganlar", ["-is_new", "-created_at"]),
    "price_asc": ("Avval arzonlari", ["price_from"]),
    "price_desc": ("Avval qimmatlari", ["-price_from"]),
    "rating": ("Reyting bo'yicha", [F("rating").desc(nulls_last=True), "-reviews_total"]),
}

# Oila kartochkalari: qisqa ta'rif va rang (bosh sahifa, katalog)
FAMILY_INFO = {
    "floral": ("Atirgul, yasmin, pion — nafis va romantik", "#E8A9B8"),
    "oriental": ("Anbar, za'faron, ziravorlar — iliq va sirli", "#C8553D"),
    "woody": ("Sandal, kedr, vetiver — chuqur va xotirjam", "#A07850"),
    "citrus": ("Bergamot, limon, greypfrut — tetik va yorqin", "#E9C46A"),
    "fougere": ("Lavanda, eman moxi — klassik erkakcha", "#4F7A7A"),
    "gourmand": ("Vanil, pralin, qahva — shirin va qulay", "#9C5A2E"),
    "chypre": ("Bergamot va pachuli — nafis kontrast", "#B88A6A"),
    "aquatic": ("Dengiz shabadasi — toza va salqin", "#7FB3C8"),
    "leather": ("Teri va tutun — jasur va xarakterli", "#5A3E2B"),
}


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def home(request):
    base = Perfume.objects.active().with_stats().prefetch_related("variants")
    bestsellers = list(base.filter(is_bestseller=True).order_by("-sold_count")[:8])
    new_arrivals = list(base.filter(is_new=True).order_by("-created_at")[:8])
    if len(new_arrivals) < 8:  # vitrina qatori to'liq bo'lishi uchun eng so'nggi chiqqanlar bilan to'ldiramiz
        new_arrivals += list(base.exclude(pk__in=[p.pk for p in new_arrivals])
                             .order_by(F("year").desc(nulls_last=True))[:8 - len(new_arrivals)])
    on_sale = list(base.filter(old_price_from__isnull=False).order_by("-sold_count")[:4])

    # Bosh banner uchun turli shakldagi uchta flakon
    hero, shapes = [], set()
    for p in bestsellers:
        if p.shape not in shapes:
            hero.append(p)
            shapes.add(p.shape)
        if len(hero) == 3:
            break

    family_counts = dict(
        Perfume.objects.active().values_list("family").annotate(n=Count("id")).values_list("family", "n"))
    families = [
        {"key": key, "label": label, "text": FAMILY_INFO[key][0], "color": FAMILY_INFO[key][1],
         "count": family_counts.get(key, 0)}
        for key, label in Perfume.Family.choices
    ]
    gender_counts = dict(
        Perfume.objects.active().values_list("gender").annotate(n=Count("id")).values_list("gender", "n"))
    popular = Perfume.objects.active().select_related("brand").order_by("-sold_count")
    catalog_url = reverse("shop:catalog")
    categories = [
        {"title": "Ayollar uchun", "url": f"{catalog_url}?gender=women", "count": gender_counts.get("women", 0),
         "tint": "#E8A9B8",
         "perfume": popular.filter(gender="women").first()},
        {"title": "Erkaklar uchun", "url": f"{catalog_url}?gender=men", "count": gender_counts.get("men", 0),
         "tint": "#8FB3CF",
         "perfume": popular.filter(gender="men").first()},
        {"title": "Uniseks", "url": f"{catalog_url}?gender=unisex", "count": gender_counts.get("unisex", 0),
         "tint": "#E3B98A",
         "perfume": popular.filter(gender="unisex").first()},
        {"title": "Nish parfyumeriya", "url": f"{catalog_url}?niche=1", "tint": "#C9AE84",
         "count": Perfume.objects.active().filter(brand__is_niche=True).count(),
         "perfume": popular.filter(brand__is_niche=True).exclude(gender="unisex").first()},
    ]

    testimonials = (Review.objects.filter(is_approved=True, rating=5, perfume__is_active=True)
                    .select_related("perfume__brand").order_by("-created_at")[:6])

    return render(request, "shop/home.html", {
        "hero": hero,
        "bestsellers": bestsellers,
        "new_arrivals": new_arrivals,
        "on_sale": on_sale,
        "families": families,
        "categories": categories,
        "brands": Brand.objects.annotate(n=Count("perfumes")).filter(n__gt=0),
        "testimonials": testimonials,
    })


def _apply_filters(request, qs):
    """GET parametrlari bo'yicha filtrlaydi. (queryset, faol filtr chiplari) qaytaradi."""
    g = request.GET
    chips = []

    q = g.get("q", "").strip()
    if q:
        note_hits = Perfume.objects.filter(
            Q(top_notes__name__icontains=q) | Q(heart_notes__name__icontains=q)
            | Q(base_notes__name__icontains=q)).values("pk")
        qs = qs.filter(Q(name__icontains=q) | Q(brand__name__icontains=q) | Q(pk__in=note_hits))
        chips.append(("q", None, f"«{q}»"))

    genders = [v for v in g.getlist("gender") if v in Perfume.Gender.values]
    if genders:
        qs = qs.filter(gender__in=genders)
        chips += [("gender", v, Perfume.Gender(v).label) for v in genders]

    brand_slugs = g.getlist("brand")
    if brand_slugs:
        qs = qs.filter(brand__slug__in=brand_slugs)
        names = dict(Brand.objects.filter(slug__in=brand_slugs).values_list("slug", "name"))
        chips += [("brand", s, names.get(s, s)) for s in brand_slugs]

    families = [v for v in g.getlist("family") if v in Perfume.Family.values]
    if families:
        qs = qs.filter(family__in=families)
        chips += [("family", v, Perfume.Family(v).label) for v in families]

    concs = [v for v in g.getlist("conc") if v in Perfume.Concentration.values]
    if concs:
        qs = qs.filter(concentration__in=concs)
        chips += [("conc", v, Perfume.Concentration(v).label) for v in concs]

    note_slug = g.get("note")
    if note_slug:
        note = Note.objects.filter(slug=note_slug).first()
        if note:
            with_note = Perfume.objects.filter(
                Q(top_notes=note) | Q(heart_notes=note) | Q(base_notes=note)).values("pk")
            qs = qs.filter(pk__in=with_note)
            chips.append(("note", None, f"Nota: {note.name}"))

    for field, lookup, label in (("min", "price_from__gte", "dan"), ("max", "price_from__lte", "gacha")):
        raw = g.get(field, "").replace(" ", "")
        if raw.isdigit():
            qs = qs.filter(**{lookup: int(raw)})
            chips.append((field, None, f"{som(int(raw))} {label}"))

    if g.get("sale"):
        qs = qs.filter(Exists(Variant.objects.filter(perfume=OuterRef("pk"), old_price__isnull=False)))
        chips.append(("sale", None, "Chegirmadagilar"))
    if g.get("new"):
        qs = qs.filter(is_new=True)
        chips.append(("new", None, "Yangi"))
    if g.get("niche"):
        qs = qs.filter(brand__is_niche=True)
        chips.append(("niche", None, "Nish parfyumeriya"))
    if g.get("stock"):
        qs = qs.filter(Exists(Variant.objects.filter(perfume=OuterRef("pk"), stock__gt=0)))
        chips.append(("stock", None, "Mavjudlari"))

    return qs, chips


def _page_title(request):
    g = request.GET
    genders = g.getlist("gender")
    if g.get("q"):
        return "Qidiruv natijalari"
    if len(genders) == 1 and genders[0] in Perfume.Gender.values:
        return {"women": "Ayollar atirlari", "men": "Erkaklar atirlari", "unisex": "Uniseks atirlar"}[genders[0]]
    if g.get("sale"):
        return "Aksiyalar va chegirmalar"
    if g.get("niche"):
        return "Nish parfyumeriya"
    if g.get("new"):
        return "Yangi kelganlar"
    families = g.getlist("family")
    if len(families) == 1 and families[0] in Perfume.Family.values:
        return f"{Perfume.Family(families[0]).label} atirlar"
    return "Barcha atirlar"


def catalog(request):
    qs = Perfume.objects.active().with_stats().prefetch_related("variants")
    qs, chips = _apply_filters(request, qs)

    sort = request.GET.get("sort", "popular")
    if sort not in SORTS:
        sort = "popular"
    qs = qs.order_by(*SORTS[sort][1], "pk")

    page = Paginator(qs, PER_PAGE).get_page(request.GET.get("page"))

    active = Perfume.objects.active()
    return render(request, "shop/catalog.html", {
        "page": page,
        "page_range": page.paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1),
        "total": page.paginator.count,
        "chips": chips,
        "title": _page_title(request),
        "sort": sort,
        "sorts": [(k, v[0]) for k, v in SORTS.items()],
        "brands": Brand.objects.filter(perfumes__in=active).annotate(n=Count("perfumes")).order_by("name"),
        "genders": Perfume.Gender.choices,
        "families": Perfume.Family.choices,
        "concentrations": Perfume.Concentration.choices,
        "selected": {
            "gender": request.GET.getlist("gender"),
            "brand": request.GET.getlist("brand"),
            "family": request.GET.getlist("family"),
            "conc": request.GET.getlist("conc"),
        },
    })


def perfume_detail(request, slug):
    perfume = get_object_or_404(
        Perfume.objects.active().with_stats().prefetch_related(
            "variants", "top_notes", "heart_notes", "base_notes"),
        slug=slug)

    reviews = list(perfume.reviews.filter(is_approved=True))
    distribution = []
    for star in range(5, 0, -1):
        n = sum(1 for r in reviews if r.rating == star)
        distribution.append({"star": star, "n": n, "pct": round(n * 100 / len(reviews)) if reviews else 0})

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.perfume = perfume
            if request.user.is_authenticated:
                review.user = request.user
            review.save()
            messages.success(request, "Rahmat! Sharhingiz qo'shildi.")
            return redirect(f"{perfume.get_absolute_url()}#sharhlar")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial["name"] = request.user.first_name or request.user.username
        form = ReviewForm(initial=initial)

    similar = list(
        Perfume.objects.active().with_stats().prefetch_related("variants")
        .filter(family=perfume.family, gender__in=[perfume.gender, Perfume.Gender.UNISEX])
        .exclude(pk=perfume.pk).order_by("-sold_count")[:4])
    if len(similar) < 4:
        similar += list(
            Perfume.objects.active().with_stats().prefetch_related("variants")
            .filter(brand=perfume.brand).exclude(pk__in=[perfume.pk, *[p.pk for p in similar]])
            [:4 - len(similar)])

    recent_ids = [pk for pk in get_recent(request) if pk != perfume.pk][:4]
    recent_map = {p.pk: p for p in Perfume.objects.active().with_stats()
                  .prefetch_related("variants").filter(pk__in=recent_ids)}
    recent = [recent_map[pk] for pk in recent_ids if pk in recent_map]
    push_recent(request, perfume.pk)

    variants = list(perfume.variants.all())
    selected = perfume.default_variant() or (variants[0] if variants else None)

    return render(request, "shop/perfume_detail.html", {
        "perfume": perfume,
        "variants": variants,
        "selected": selected,
        "reviews": reviews,
        "distribution": distribution,
        "form": form,
        "similar": similar,
        "recent": recent,
        "pyramid": [
            ("Yuqori notalar", "Birinchi 15 daqiqa", perfume.top_notes.all()),
            ("Yurak notalari", "2 — 4 soat", perfume.heart_notes.all()),
            ("Asos notalari", "Kun bo'yi", perfume.base_notes.all()),
        ],
    })


def brands(request):
    brand_list = Brand.objects.annotate(n=Count("perfumes", filter=Q(perfumes__is_active=True)))
    groups = {}
    for b in brand_list:
        groups.setdefault(b.name[0].upper(), []).append(b)
    return render(request, "shop/brands.html", {
        "groups": sorted(groups.items()),
        "niche": [b for b in brand_list if b.is_niche],
        "total": len(brand_list),
    })


def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    sort = request.GET.get("sort", "popular")
    if sort not in SORTS:
        sort = "popular"
    perfumes = (Perfume.objects.active().with_stats().prefetch_related("variants")
                .filter(brand=brand).order_by(*SORTS[sort][1], "pk"))
    return render(request, "shop/brand_detail.html", {
        "brand": brand,
        "perfumes": perfumes,
        "sort": sort,
        "sorts": [(k, v[0]) for k, v in SORTS.items()],
    })


def wishlist(request):
    ids = get_wishlist(request)
    found = {p.pk: p for p in Perfume.objects.active().with_stats()
             .prefetch_related("variants").filter(pk__in=ids)}
    return render(request, "shop/wishlist.html", {"perfumes": [found[i] for i in ids if i in found]})


@require_POST
def wishlist_toggle(request, pk):
    perfume = get_object_or_404(Perfume.objects.active(), pk=pk)
    added = toggle_wishlist(request, perfume.pk)
    if _is_ajax(request):
        return JsonResponse({"added": added, "count": len(get_wishlist(request))})
    messages.success(request, "Sevimlilarga qo'shildi" if added else "Sevimlilardan olib tashlandi")
    return redirect(request.POST.get("next") or reverse("shop:wishlist"))


def search_suggest(request):
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})
    perfumes = (Perfume.objects.active().with_stats()
                .filter(Q(name__icontains=q) | Q(brand__name__icontains=q))
                .order_by("-sold_count")[:6])
    brands_hit = Brand.objects.filter(name__icontains=q)[:3]
    return JsonResponse({
        "results": [
            {"title": p.name, "brand": p.brand.name, "url": p.get_absolute_url(),
             "price": som(p.price_from), "color": p.color}
            for p in perfumes
        ],
        "brands": [{"title": b.name, "url": b.get_absolute_url()} for b in brands_hit],
        "all_url": f"{reverse('shop:catalog')}?{urlencode({'q': q})}",
    })


QUIZ = [
    {"name": "gender", "title": "Atir kim uchun?", "options": [
        ("women", "Ayol uchun", "Nafis, gulli va shirin kompozitsiyalar"),
        ("men", "Erkak uchun", "Yog'ochli, ziravorli va tetik hidlar"),
        ("unisex", "Farqi yo'q", "Hamma uchun mos uniseks atirlar"),
    ]},
    {"name": "family", "title": "Qaysi hidlar sizga yoqadi?", "options": [
        ("floral", "Gullar", "Atirgul, yasmin, pion"),
        ("gourmand", "Shirinliklar", "Vanil, karamel, qahva"),
        ("oriental", "Sharqona", "Anbar, za'faron, ud"),
        ("woody", "Yog'och", "Sandal, kedr, vetiver"),
        ("citrus", "Sitrus va tetiklik", "Bergamot, limon, dengiz"),
        ("fougere", "Klassik erkakcha", "Lavanda, yalpiz, moxlar"),
    ]},
    {"name": "time", "title": "Qachon sepasiz?", "options": [
        ("day", "Kundalik / ofis", "Yengil va yoqimli, atrofdagilarni bezovta qilmaydi"),
        ("evening", "Kechki tadbirlar", "Yorqin va esda qolarli"),
        ("any", "Har doim", "Universal hid"),
    ]},
    {"name": "budget", "title": "Taxminiy byudjet?", "options": [
        ("1", "1 mln so'mgacha", "Hamyonbop, ammo sifatli"),
        ("2", "1 — 3 mln so'm", "Mashhur dizayner brendlar"),
        ("3", "3 mln so'mdan yuqori", "Nish va hashamatli"),
        ("any", "Muhim emas", "Eng mosini ko'rsating"),
    ]},
]

# Oila tanlanganda unga «qarindosh» oilalar ham qisman ball oladi
RELATED_FAMILIES = {
    "floral": {"chypre"}, "gourmand": {"oriental"}, "oriental": {"gourmand", "leather", "woody"},
    "woody": {"leather", "oriental"}, "citrus": {"aquatic", "fougere"}, "fougere": {"citrus", "aquatic"},
}
BUDGETS = {"1": (0, 1_000_000), "2": (1_000_000, 3_000_000), "3": (3_000_000, 10**9)}


def quiz(request):
    answers = {step["name"]: request.GET.get(step["name"]) for step in QUIZ}
    results = None
    if all(answers.values()):
        qs = Perfume.objects.active().with_stats().prefetch_related("variants")
        if answers["gender"] in ("women", "men"):
            qs = qs.filter(gender__in=[answers["gender"], Perfume.Gender.UNISEX])
        scored = []
        for p in qs:
            score = 0
            if p.family == answers["family"]:
                score += 5
            elif p.family in RELATED_FAMILIES.get(answers["family"], set()):
                score += 2
            if p.gender == answers["gender"]:
                score += 1
            if answers["time"] == "any" or p.time_of_day in (answers["time"], "any"):
                score += 2
            low, high = BUDGETS.get(answers["budget"], (0, 10**9))
            if p.price_from and low <= p.price_from < high:
                score += 2
            score += min(p.sold_count, 1000) / 1000  # teng ball bo'lsa — ommaboplari oldinda
            scored.append((score, p))
        scored.sort(key=lambda t: t[0], reverse=True)
        results = []
        for score, p in scored[:6]:
            p.match = min(99, round(score / 11 * 100))
            results.append(p)
    return render(request, "shop/quiz.html", {"steps": QUIZ, "answers": answers, "results": results})
