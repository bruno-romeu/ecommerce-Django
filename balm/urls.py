from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from inngest.django import serve
from inngest_functions.send_verification_email import send_verification_email_fn
from inngest_functions.process_shipping import process_shipping_fn
from ecommerce_inngest import inngest_client
from django.conf import settings
from django.conf.urls.static import static

@csrf_exempt
def inngest_view(request):
    return serve(
        request,
        inngest_client,
        [
            send_verification_email_fn,
            process_shipping_fn,
        ],
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apis.urls')),
    path("api/inngest/", inngest_view, name="inngest"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)