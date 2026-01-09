from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import inngest.django
from ecommerce_inngest import inngest_client
from .send_verification_email import send_verification_email_fn
from .process_shipping import process_shipping_fn

handler = inngest.django.serve(
    inngest_client,
    [send_verification_email_fn, process_shipping_fn]
)

@csrf_exempt
@require_http_methods(["GET", "PUT", "POST"])
def inngest_view(request):
    """
    View que processa requests do Inngest
    """
    return handler(request)