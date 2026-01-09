from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from inngest_functions.views import inngest_endpoint
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apis.urls')),
    path("api/inngest/", inngest_endpoint),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)