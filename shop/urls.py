from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.home, name="home"),
    path("katalog/", views.catalog, name="catalog"),
    path("atir/<slug:slug>/", views.perfume_detail, name="perfume"),
    path("brendlar/", views.brands, name="brands"),
    path("brendlar/<slug:slug>/", views.brand_detail, name="brand"),
    path("sevimlilar/", views.wishlist, name="wishlist"),
    path("sevimlilar/<int:pk>/", views.wishlist_toggle, name="wishlist_toggle"),
    path("atir-tanlash/", views.quiz, name="quiz"),
    path("api/qidiruv/", views.search_suggest, name="search_suggest"),
]
