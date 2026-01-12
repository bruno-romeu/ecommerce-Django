from inngest import Context, TriggerEvent
import traceback
from asgiref.sync import sync_to_async
from ecommerce_inngest import inngest_client
from accounts.models import CustomUser
from django.core.mail import send_mail
from django.conf import settings

@inngest_client.create_function(
    fn_id="send-verification-email",
    trigger=TriggerEvent(event="auth/send.verification.email"),
    retries=3 
)
async def send_verification_email_fn(ctx: Context):
    print(f"\n{'=' * 60}")
    print(f"[INNGEST EMAIL] Função de email iniciada")
    print(f"[INNGEST EMAIL] Event data: {ctx.event.data}")
    print(f"{'=' * 60}\n")

    
    data = ctx.event.data
    user_id = data.get("user_id")
    token = data.get("token")
    frontend_url = data.get("frontend_url")

    if not all([user_id, token, frontend_url]):
        print("[INNGEST EMAIL] ERRO: Dados incompletos")
        return {"status": "error", "message": "Dados incompletos"}

    print(f"[INNGEST EMAIL] User ID: {user_id}")
    print(f"[INNGEST EMAIL] Frontend URL: {frontend_url}")

    async def send_email_step():
        print(f"[INNGEST EMAIL] Django configurado, buscando usuário...")

        try:
            @sync_to_async
            def get_user():
                return CustomUser.objects.get(id=user_id)

            user = await get_user()
            print(f"[INNGEST EMAIL] Usuário encontrado: {user.email}")
        except CustomUser.DoesNotExist:
            return {"status": "error", "message": f"Usuário {user_id} não encontrado", "abort": True}

        verification_url = f"{frontend_url}/verificar-email/{token}"

        print(f"[INNGEST EMAIL] Preparando email para {user.email}...")

        await sync_to_async(send_mail)(
            subject='Verifique seu email - Balm',
            message=f'''Olá {user.first_name},
            
            Obrigado por se registrar na Balm!
            Para completar seu cadastro, clique no link abaixo:
            {verification_url}
            ''',
            html_message=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .button {{ 
                        display: inline-block; padding: 12px 30px; 
                        background-color: #007bff; color: white; 
                        text-decoration: none; border-radius: 5px; 
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Olá {user.first_name},</h2>
                    <p>Obrigado por se cadastrar na Velas Balm!</p>
                    <center>
                        <a href="{verification_url}" class="button">Verificar Email</a>
                    </center>
                </div>
            </body>
            </html>
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        print(f"[INNGEST EMAIL] ✓ Email enviado com sucesso para {user.email}")
        return {
            "status": "success",
            "email_sent": True,
            "recipient": user.email
        }

    result = await ctx.step.run("sending-django-email", send_email_step)

    if result.get("abort"):
        return result

    print(f"\n{'=' * 60}")
    print(f"[INNGEST EMAIL] Job concluído com sucesso")
    print(f"{'=' * 60}\n")

    return result