from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from inngest.django import serve
from ecommerce_inngest import inngest_client
from .send_verification_email import send_verification_email_fn
from .process_shipping import process_shipping_fn

inngest_serve = serve(
    inngest_client,
    [send_verification_email_fn, process_shipping_fn],
)

@csrf_exempt
def inngest_endpoint(request):
    return inngest_serve(request)