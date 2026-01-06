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


def send_verification_email(user, frontend_url=None):
    """
    Prepara o usuário e dispara o EVENTO do Inngest.
    Retorna True se o evento foi disparado com sucesso.
    """
    if not frontend_url:
        frontend_url = os.getenv('FRONTEND_URL',
                                 settings.FRONTEND_URL)

    # Gera novo token
    token = generate_verification_token()
    user.email_verification_token = token
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=['email_verification_token',
                             'email_verification_sent_at'])

    logger.info(f"Token gerado para usuário {user.email}")

    try:
        # Dispara o evento Inngest de forma síncrona
        async_to_sync(inngest_client.send)(
            inngest.Event(
                name="auth/send.verification.email",
                data={
                    "user_id": user.id,
                    "token": token,
                    "frontend_url": frontend_url
                }
            )
        )

        logger.info(f"Evento Inngest disparado com sucesso para {user.email}")
        return True

    except Exception as e:
        logger.error(f"Erro ao disparar evento Inngest para {user.email}: {str(e)}")
        logger.exception(e)
        return False


def is_verification_token_valid(user):
    """
    Verifica se o token de verificação ainda é válido (menos de 24h)
    """
    if not user.email_verification_sent_at:
        return False

    expiry_time = user.email_verification_sent_at + timedelta(hours=24)
    return timezone.now() < expiry_time