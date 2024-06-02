from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("api.urls")),
    path("api/", include("api.urls")),
    path("webapi/", include("webapi.urls")),
    path("family_registeration/api/", include("family_registeration.urls")),
    path("family_link/api/", include("family_link.urls")),
    path("FamFin/api/", include("FamFin.urls")),
    path("Grandma_Task_Management/api/", include("Grandma_Task_Management.urls")),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 