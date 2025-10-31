from django_ratelimit.exceptions import Ratelimited
from django.utils.deprecation import MiddlewareMixin
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
        

class JWTAuthCookieMiddleware(MiddlewareMixin):
    """
    Middleware que extrai JWT do cookie e adiciona ao header Authorization
    """
    def process_request(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')
        
        if access_token:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        
        return None