import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
import os

logger = logging.getLogger(__name__)

def generate_verification_token():
    """Gera um token único para verificação de email"""
    return secrets.token_urlsafe(32)

def send_verification_email(user, frontend_url=None):
    """
    Envia email de verificação para o usuário
    
    Args:
        user: Instância do CustomUser
        frontend_url: URL base do frontend (opcional, usa env se não fornecido)
    """
    if not frontend_url:
        frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'
    
    token = generate_verification_token()
    user.email_verification_token = token
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
    
    verification_url = f"{frontend_url}/verificar-email/{token}"
    
    subject = 'Verifique seu email - Velas Balm'
    message = f"""
Olá {user.first_name},

Obrigado por se cadastrar na Velas Balm!

Para completar seu cadastro, por favor clique no link abaixo para verificar seu email:

{verification_url}

Este link expira em 24 horas.

Se você não criou esta conta, por favor ignore este email.

Atenciosamente,
Equipe Velas Balm
    """
    
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #021f59; padding: 20px; text-align: center; }}
        .title {{color: #fff}}
        .content {{ padding: 20px; }}
        .button {{ 
            display: inline-block; 
            padding: 12px 30px; 
            background-color: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 20px 0;
        }}
        a {{color: #fff}}
        .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">Velas Balm</h1>
        </div>
        <div class="content">
            <h2>Olá {user.first_name},</h2>
            <p>Obrigado por se cadastrar na Velas Balm!</p>
            <p>Para completar seu cadastro, por favor clique no botão abaixo para verificar seu email:</p>
            <center>
                <a href="{verification_url}" class="button">Verificar Email</a>
            </center>
            <p>Ou copie e cole este link no seu navegador:</p>
            <p style="word-break: break-all; color: #007bff;">{verification_url}</p>
            <p class="footer">
                Este link expira em 24 horas.<br>
                Se você não criou esta conta, por favor ignore este email.
            </p>
        </div>
    </div>
</body>
</html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Email de verificação enviado para {user.email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email de verificação para {user.email}: {str(e)}")
        return False

def is_verification_token_valid(user):
    """
    Verifica se o token de verificação ainda é válido (menos de 24 horas)
    
    Args:
        user: Instância do CustomUser
        
    Returns:
        bool: True se válido, False caso contrário
    """
    if not user.email_verification_sent_at:
        return False
    
    expiry_time = user.email_verification_sent_at + timedelta(hours=24)
    return timezone.now() < expiry_time