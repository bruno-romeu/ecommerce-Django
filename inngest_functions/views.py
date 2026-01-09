from django.views.decorators.csrf import csrf_exempt
import inngest.django
from ecommerce_inngest import inngest_client
from .send_verification_email import send_verification_email_fn
from .process_shipping import process_shipping_fn


# Cria o handler usando o módulo oficial do Django
# serve() retorna um URLPattern, mas podemos acessar o handler interno
_inngest_serve = inngest.django.serve(
    inngest_client,
    [send_verification_email_fn, process_shipping_fn]
)

# Extrai a view callable do URLPattern
# URLPattern tem um atributo 'callback' que é a view real
inngest_endpoint = _inngest_serve.callback