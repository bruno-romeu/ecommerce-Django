from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from inngest_functions.urls import inngest_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/inngest/', inngest_view), 
    path('api/', include('apis.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)