from django.contrib import admin
from django.urls import path, include
from inngest.django import serve
from inngest_functions.send_verification_email import send_verification_email_fn
from inngest_functions.process_shipping import process_shipping_fn
from ecommerce_inngest import inngest_client
from django.conf import settings
from django.conf.urls.static import static
from inngest_functions.views import inngest_endpoint


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apis.urls')),
    path("api/inngest", inngest_endpoint),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
