from django_ratelimit.decorators import ratelimit, Ratelimited
from django.http import JsonResponse
from functools import wraps
from apis.utils.security_logger import log_security_event, get_client_ip


def rate_limit_handler(request, exception):
    """
    Função que retorna uma resposta amigável quando o limite é atingido
    """
    return JsonResponse({
        'error': 'Muitas tentativas. Por favor, aguarde alguns minutos antes de tentar novamente.',
        'detail': 'Rate limit exceeded'
    }, status=429)

# -------- AUTENTICAÇÃO --------
def ratelimit_login(func):
    """Login: 5 tentativas / 15 minutos"""
    @wraps(func)
    @ratelimit(key='ip', rate='5/15m', method='POST', block=True)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except Ratelimited:
            log_security_event(
                event_type='RATE_LIMIT_LOGIN',
                request=request,
                details=f'IP {get_client_ip(request)} atingiu limite de tentativas de login',
                level='warning'
            )
            return JsonResponse({
                'error': 'Muitas tentativas de login. Aguarde 15 minutos.'
            }, status=429)
    return wrapper

def ratelimit_register(func):
    """Registro: 3 cadastros / 1 hora"""
    @wraps(func)
    @ratelimit(key='ip', rate='3/1h', method='POST', block=True)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except Ratelimited:
            log_security_event(
                event_type='RATE_LIMIT_REGISTER',
                request=request,
                details=f'IP {get_client_ip(request)} atingiu limite de cadastros',
                level='warning'
            )
            return JsonResponse({
                'error': 'Muitas tentativas de cadastro. Aguarde 1 hora.'
            }, status=429)
    return wrapper

def ratelimit_password_reset(func):
    """Reset senha: 3 tentativas / 1 hora por email"""
    @wraps(func)
    @ratelimit(key='ip', rate='3/1h', method='POST', block=True)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return wrapper

# -------- CHECKOUT/PAGAMENTO --------
def ratelimit_create_order(func):
    """Criar pedido: 10 pedidos / 1 hora por usuário"""
    @wraps(func)
    @ratelimit(key='user', rate='10/1h', method='POST', block=True)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return wrapper

def ratelimit_payment(func):
    """Pagamento: 15 tentativas / 1 hora por usuário"""
    @wraps(func)
    @ratelimit(key='user', rate='15/1h', method='POST', block=True)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return wrapper

def ratelimit_shipping(func):
    """Calcular frete: 20 cálculos / 1 hora por IP"""
    @wraps(func)
    @ratelimit(key='ip', rate='20/1h', method='POST', block=True)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return wrapper

# -------- MODIFICAÇÃO DE DADOS --------
def ratelimit_profile_update(func):
    """Atualizar perfil: 10 atualizações / 1 hora"""
    @wraps(func)
    @ratelimit(key='user', rate='10/1h', method=['PATCH', 'PUT'], block=True)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return wrapper

def ratelimit_address(func):
    """Criar/atualizar endereço: 15 operações / 1 hora"""
    @wraps(func)
    @ratelimit(key='user', rate='15/1h', method=['POST', 'PATCH', 'PUT'], block=True)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return wrapper

def ratelimit_cart(func):
    """Adicionar ao carrinho: 30 adições / 5 minutos"""
    @wraps(func)
    @ratelimit(key='user_or_ip', rate='30/5m', method='POST', block=True)
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return wrapper