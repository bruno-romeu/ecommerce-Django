from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_verification_email_task(self, user_id, token, frontend_url):
    """
    Task Celery para enviar email de verificação de forma assíncrona.
    Recebe ID do usuário e token para evitar problemas de serialização.
    """
    try:
        user = User.objects.get(id=user_id)
        
        verification_url = f"{frontend_url}/verificar-email/{token}"
        
        subject = 'Verifique seu email - Velas Balm'
        message = f"""
Olá {user.first_name},

Obrigado por se cadastrar na Velas Balm!
Para completar seu cadastro, por favor clique no link abaixo:
{verification_url}

Este link expira em 24 horas.
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

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Email de verificação enviado via Celery para {user.email}")
        return True

    except User.DoesNotExist:
        logger.error(f"Usuário ID {user_id} não encontrado na task de email.")
    except Exception as e:
        logger.error(f"Erro na task de email para user {user_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)