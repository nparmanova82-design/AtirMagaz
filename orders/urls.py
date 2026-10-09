from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("savatcha/", views.cart_detail, name="cart"),
    path("savatcha/qoshish/", views.cart_add, name="cart_add"),
    path("savatcha/yangilash/", views.cart_update, name="cart_update"),
    path("savatcha/ochirish/", views.cart_remove, name="cart_remove"),
    path("savatcha/promokod/", views.promo_apply, name="promo_apply"),
    path("savatcha/promokod/bekor/", views.promo_remove, name="promo_remove"),
    path("rasmiylashtirish/", views.checkout, name="checkout"),
    path("buyurtma/<str:number>/", views.success, name="success"),
    path("buyurtma-holati/", views.track, name="track"),
    path("api/savatcha/", views.cart_summary, name="cart_summary"),
]
