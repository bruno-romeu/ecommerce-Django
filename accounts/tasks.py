from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
import logging
import resend

logger = logging.getLogger(__name__)
User = get_user_model()

resend.api_key = settings.RESEND_API_KEY

@shared_task(bind=True, max_retries=3)
def send_verification_email_task(self, user_id, token, frontend_url):
    """
    Task Celery para enviar email de verificação de forma assíncrona.
    Recebe ID do usuário e token para evitar problemas de serialização.
    """
    try:
        user = User.objects.get(id=user_id)
        verification_url = f"{frontend_url}/verificar-email/{token}"
        
        logger.info(f"[RESEND] Iniciando envio para {user.email}")

        html_content = f"""
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
                    display: inline-block; padding: 12px 30px; background-color: #007bff; 
                    color: white; text-decoration: none; border-radius: 5px; margin: 20px 0;
                }}
                a {{color: #fff}}
                .footer {{ font-size: 12px; color: #666; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header"><h1 class="title">Velas Balm</h1></div>
                <div class="content">
                    <h2>Olá {user.first_name},</h2>
                    <p>Obrigado por se cadastrar na Velas Balm!</p>
                    <p>Para completar seu cadastro, clique no botão abaixo:</p>
                    <center><a href="{verification_url}" class="button">Verificar Email</a></center>
                    <p>Ou copie este link: {verification_url}</p>
                </div>
            </div>
        </body>
        </html>
        """

        params = {
            "from": settings.RESEND_FROM_EMAIL,
            "to": [user.email],
            "subject": "Verifique seu email - Velas Balm",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        
        logger.info(f"✅ [RESEND] Sucesso! ID do email: {email.get('id')}")
        return email

    except User.DoesNotExist:
        logger.error(f"❌ [RESEND] Usuário {user_id} não encontrado.")
    except Exception as e:
        logger.error(f"❌ [RESEND] Falha ao enviar: {e}")
        raise self.retry(exc=e, countdown=10)