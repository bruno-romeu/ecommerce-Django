import secrets
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
from .tasks import send_verification_email_task 

logger = logging.getLogger(__name__)

def generate_verification_token():
    """Gera um token único para verificação de email"""
    return secrets.token_urlsafe(32)

def send_verification_email(user, frontend_url=None):
    """
    Prepara o usuário para verificação e dispara a task do Celery.
    """
    if not frontend_url:
        frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'
    
    token = generate_verification_token()
    user.email_verification_token = token
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
    
    try:
        send_verification_email_task.delay(user.id, token, frontend_url)
        logger.info(f"Task de email disparada para o usuário {user.email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao disparar task do Celery: {e}")
        return True 

def is_verification_token_valid(user):
    if not user.email_verification_sent_at:
        return False
    
    expiry_time = user.email_verification_sent_at + timedelta(hours=24)
    return timezone.now() < expiry_time