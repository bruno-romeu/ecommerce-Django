from django.views.decorators.csrf import csrf_exempt
from inngest.django import serve
from ecommerce_inngest import inngest_client

@csrf_exempt
def inngest_endpoint(request):
    """
    Endpoint para o Inngest
    """
    return serve(inngest_client, request)