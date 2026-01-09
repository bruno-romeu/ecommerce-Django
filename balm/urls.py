from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from inngest.django import serve
from ecommerce_inngest import inngest_client
from inngest_functions.send_verification_email import send_verification_email_fn
from inngest_functions.process_shipping import process_shipping_fn

inngest_view = serve(
    inngest_client,
    [send_verification_email_fn, process_shipping_fn],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/inngest/', inngest_view), 
    path('api/', include('apis.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)