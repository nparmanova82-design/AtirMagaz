from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from shop.models import Perfume, Variant
from shop.templatetags.shop_tags import som

from .cart import Cart, quote
from .forms import CheckoutForm, TrackForm
from .models import Order, OrderItem, PromoCode

MY_ORDERS_KEY = "my_orders"


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _int(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def cart_detail(request):
    cart = Cart(request)
    promo = cart.promo()
    return render(request, "orders/cart.html", {
        "lines": cart.lines(),
        "promo": promo,
        "totals": quote(cart.subtotal, promo),
    })


@require_POST
def cart_add(request):
    variant = get_object_or_404(Variant.objects.select_related("perfume__brand"),
                                pk=_int(request.POST.get("variant")), perfume__is_active=True)
    cart = Cart(request)
    if variant.stock == 0:
        text, ok = "Afsuski, bu hajm hozircha tugagan.", False
    else:
        before = cart.quantity_of(variant.pk)
        after = cart.add(variant, max(1, _int(request.POST.get("quantity"))))
        ok = after > before
        text = (f"{variant.perfume} ({variant.label}) savatchaga qo'shildi" if ok
                else f"Omborda faqat {variant.stock} dona bor — hammasi savatchada.")
    if _is_ajax(request):
        return JsonResponse({"ok": ok, "message": text, "count": len(cart)})
    (messages.success if ok else messages.warning)(request, text)
    return redirect(request.POST.get("next") or reverse("orders:cart"))


@require_POST
def cart_update(request):
    variant = get_object_or_404(Variant, pk=_int(request.POST.get("variant")))
    Cart(request).add(variant, _int(request.POST.get("quantity"), 0), replace=True)
    return redirect("orders:cart")


@require_POST
def cart_remove(request):
    Cart(request).remove(_int(request.POST.get("variant"), 0))
    messages.info(request, "Mahsulot savatchadan olib tashlandi.")
    return redirect("orders:cart")


@require_POST
def promo_apply(request):
    code = request.POST.get("code", "").strip().upper()
    cart = Cart(request)
    if PromoCode.objects.filter(code=code, is_active=True).exists():
        cart.set_promo(code)
        messages.success(request, f"{code} promokodi qo'llandi.")
    else:
        messages.error(request, "Bunday promokod topilmadi yoki muddati tugagan.")
    return redirect("orders:cart")


@require_POST
def promo_remove(request):
    Cart(request).drop_promo()
    return redirect("orders:cart")


def checkout(request):
    cart = Cart(request)
    lines = cart.lines()
    if not lines:
        messages.info(request, "Savatchangiz bo'sh.")
        return redirect("orders:cart")
    promo = cart.promo()

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = _place_order(request, cart, form, promo)
            if order:
                request.session[MY_ORDERS_KEY] = [order.number, *request.session.get(MY_ORDERS_KEY, [])][:20]
                return redirect("orders:success", number=order.number)
            return redirect("orders:cart")
    else:
        initial = {}
        if request.user.is_authenticated:
            user = request.user
            initial = {"full_name": user.get_full_name() or user.first_name,
                       "phone": user.username if user.username.startswith("+998") else "",
                       "email": user.email}
            last = user.orders.first()
            if last:
                initial.update(region=last.region, address=last.address)
        form = CheckoutForm(initial=initial)

    data = form.data if form.is_bound else form.initial
    totals = quote(cart.subtotal, promo, region=data.get("region", "tashkent"),
                   delivery=data.get("delivery", Order.Delivery.COURIER),
                   gift_wrap=bool(data.get("gift_wrap")))
    return render(request, "orders/checkout.html", {
        "form": form, "lines": lines, "promo": promo, "totals": totals, "shop": settings.SHOP,
    })


@transaction.atomic
def _place_order(request, cart, form, promo):
    lines = cart.lines()
    variants = {v.pk: v for v in Variant.objects.select_for_update()
                .filter(pk__in=[line["variant"].pk for line in lines])}
    for line in lines:
        variant = variants[line["variant"].pk]
        if variant.stock < line["quantity"]:
            cart.add(variant, variant.stock, replace=True)
            messages.error(request, f"{line['perfume']} ({variant.label}) omborda {variant.stock} dona qoldi — "
                                    "savatcha yangilandi, iltimos tekshirib qayta urinib ko'ring.")
            return None

    order = form.save(commit=False)
    if request.user.is_authenticated:
        order.user = request.user
    totals = quote(cart.subtotal, promo, order.region, order.delivery, order.gift_wrap)
    order.promo_code = promo.code if promo and totals["discount"] else ""
    order.subtotal = totals["subtotal"]
    order.discount = totals["discount"]
    order.delivery_cost = totals["delivery_cost"]
    order.gift_wrap_cost = totals["gift_wrap_cost"]
    order.total = totals["total"]
    order.save()

    for line in lines:
        variant = variants[line["variant"].pk]
        OrderItem.objects.create(
            order=order, variant=variant, title=str(line["perfume"]), volume_label=variant.label,
            price=variant.price, quantity=line["quantity"])
        Variant.objects.filter(pk=variant.pk).update(stock=F("stock") - line["quantity"])
        Perfume.objects.filter(pk=variant.perfume_id).update(sold_count=F("sold_count") + line["quantity"])

    cart.clear()
    return order


def success(request, number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), number=number)
    owns = number in request.session.get(MY_ORDERS_KEY, []) or (
        request.user.is_authenticated and order.user_id == request.user.pk)
    if not owns:
        raise Http404
    return render(request, "orders/success.html", {"order": order})


def track(request):
    order = None
    form = TrackForm(request.GET or None)
    if form.is_valid():
        order = (Order.objects.prefetch_related("items")
                 .filter(number=form.cleaned_data["number"], phone=form.cleaned_data["phone"]).first())
        if not order:
            form.add_error(None, "Bunday raqam va telefon bilan buyurtma topilmadi.")
    return render(request, "orders/track.html", {"form": form, "order": order})


def cart_summary(request):
    """Sarlavhadagi savatcha hisoblagichi uchun (JS)."""
    cart = Cart(request)
    return JsonResponse({"count": len(cart), "subtotal": som(cart.subtotal)})
