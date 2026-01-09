import os
import secrets
import uuid
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
import inngest
from ecommerce_inngest import inngest_client
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Gera um token único para verificação de email"""
    return secrets.token_urlsafe(32)


def send_verification_email(user, token=None, frontend_url=None):
    """
    Dispara evento Inngest para enviar email de verificação
        
    Args:
        user: Objeto CustomUser
        token: Token de verificação (opcional, será gerado se não fornecido)
        frontend_url: URL do frontend (opcional, usa settings.FRONTEND_URL se não fornecido)
    
    Returns:
        bool: True se o evento foi disparado com sucesso, False caso contrário
    """
    try:
        if token is None:
            token = generate_verification_token()
            user.email_verification_token = token
            user.email_verification_sent_at = timezone.now()
            user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
            logger.info(f"Token gerado e salvo para usuário {user.email}")
        else:
            logger.info(f"Usando token existente para usuário {user.email}")
        
        if frontend_url is None:
            frontend_url = settings.FRONTEND_URL
        
        event_id = f"verify-email-{user.id}-{uuid.uuid4().hex[:12]}"
        
        async_to_sync(inngest_client.send)(
            inngest.Event(
                name="auth/send.verification.email",
                data={
                    "user_id": user.id,
                    "token": token,
                    "frontend_url": frontend_url,
                },
                id=event_id, 
            )
        )
        
        logger.info(f"✓ Evento Inngest disparado com sucesso para {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao disparar evento Inngest para {user.email}:")
        logger.error("", exc_info=True)
        return False 


def is_verification_token_valid(user):
    """
    Verifica se o token de verificação ainda é válido (menos de 24h)
    """
    if not user.email_verification_sent_at:
        return False

    expiry_time = user.email_verification_sent_at + timedelta(hours=24)
    return timezone.now() < expiry_time