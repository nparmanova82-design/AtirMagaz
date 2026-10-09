from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "AtirMagaz — boshqaruv paneli"
admin.site.site_title = "AtirMagaz admin"
admin.site.index_title = "Do'kon boshqaruvi"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("shop.urls")),
    path("", include("orders.urls")),
    path("", include("pages.urls")),
    path("hisob/", include("accounts.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "pages.views.not_found"
