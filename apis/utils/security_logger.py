import logging
from functools import wraps
from django.utils import timezone

security_logger = logging.getLogger('security')

def get_client_ip(request):
    """Pega o IP real do cliente (considera proxies)"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_security_event(event_type, request, user=None, details=None, level='warning'):
    """
    Registra eventos de segurança
    
    Args:
        event_type: Tipo do evento (ex: 'login_failed', 'rate_limit_hit')
        request: Objeto request do Django
        user: Usuário (se autenticado)
        details: Detalhes adicionais
        level: 'info', 'warning', 'error', 'critical'
    """
    ip = get_client_ip(request)
    if user and hasattr(user, 'email') and user.is_authenticated:
        username = user.email
    else:
        username = 'Anonymous'
    
    message = f"{event_type}"
    if details:
        message += f" | {details}"
    
    log_data = {
        'extra': {
            'ip': ip,
            'user': username,
            'event': event_type,
            'timestamp': timezone.now().isoformat(),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        }
    }
    
    if level == 'info':
        security_logger.info(message, **log_data)
    elif level == 'warning':
        security_logger.warning(message, **log_data)
    elif level == 'error':
        security_logger.error(message, **log_data)
    elif level == 'critical':
        security_logger.critical(message, **log_data)