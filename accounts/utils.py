import os
import secrets
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
import inngest
from inngest_functions.send_verification_email import inngest_client
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Gera um token único para verificação de email"""
    return secrets.token_urlsafe(32)


def send_verification_email(user, token, frontend_url):
    """
    Dispara evento Inngest para enviar email de verificação
    """
    try:
        logger.info(f"Token gerado para usuário {user.email}")
        
        event_id = f"verify-email-{user.id}-{token}"
        
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
        raise

def is_verification_token_valid(user):
    """
    Verifica se o token de verificação ainda é válido (menos de 24h)
    """
    if not user.email_verification_sent_at:
        return False

    expiry_time = user.email_verification_sent_at + timedelta(hours=24)
    return timezone.now() < expiry_time