from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = "AtirMagaz — boshqaruv paneli"
admin.site.site_title = "AtirMagaz admin"
admin.site.index_title = "Do'kon boshqaruvi"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("shop.urls")),
    path("", include("orders.urls")),
    path("", include("pages.urls")),
    path("hisob/", include("accounts.urls")),
    # Admin orqali yuklangan atir rasmlari (kichik do'kon uchun Django'ning o'zi beradi)
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

handler404 = "pages.views.not_found"
