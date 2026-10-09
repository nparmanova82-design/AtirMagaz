from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("kirish/", views.SignInView.as_view(), name="login"),
    path("chiqish/", LogoutView.as_view(), name="logout"),
    path("royxatdan-otish/", views.register, name="register"),
    path("", views.profile, name="profile"),
]
