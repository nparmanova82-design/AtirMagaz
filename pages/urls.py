from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("biz-haqimizda/", views.about, name="about"),
    path("aloqa/", views.contacts, name="contacts"),
    path("yetkazib-berish/", views.delivery, name="delivery"),
    path("savollar/", views.faq, name="faq"),
    path("qaytarish/", views.returns, name="returns"),
    path("qollanma/", views.guide, name="guide"),
    path("obuna/", views.subscribe, name="subscribe"),
]
