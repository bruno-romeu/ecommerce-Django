from django.contrib import admin
from django.urls import path, include
from inngest.django import serve
from ecommerce_inngest import inngest_client, send_verification_email_fn
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apis.urls')),
    serve(inngest_client, [send_verification_email_fn]),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
