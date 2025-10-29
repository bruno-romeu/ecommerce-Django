from django_ratelimit.exceptions import Ratelimited
from django.http import JsonResponse

class RateLimitMiddleware:
    """
    Middleware para capturar exceções de rate limit
    e retornar uma resposta amigável
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            return JsonResponse({
                'error': 'Você fez muitas requisições. Por favor, aguarde um pouco.',
                'detail': 'Rate limit excedido. Tente novamente em alguns minutos.'
            }, status=429)