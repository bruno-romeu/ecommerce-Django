import inngest
from inngest import Context, Step, TriggerEvent
import traceback
from asgiref.sync import sync_to_async

inngest_client = inngest.Inngest(
    app_id="ecommerce_app",
    is_production=False,
)



@inngest_client.create_function(
    fn_id="send-verification-email",
    trigger=TriggerEvent(event="auth/send.verification.email"),
)
async def send_verification_email_fn(ctx: Context):
    """
    Função Inngest para enviar email de verificação
    """
    print(f"\n{'=' * 60}")
    print(f"[INNGEST] Função de email iniciada")
    print(f"[INNGEST] Event data: {ctx.event.data}")
    print(f"{'=' * 60}\n")

    try:
        data = ctx.event.data
        user_id = data.get("user_id")
        token = data.get("token")
        frontend_url = data.get("frontend_url")

        if not all([user_id, token, frontend_url]):
            raise ValueError("Dados incompletos no evento")

        print(f"[INNGEST] User ID: {user_id}")
        print(f"[INNGEST] Frontend URL: {frontend_url}")

        async def send_email_step():
            # Imports dentro da função para evitar problemas de contexto
            import django
            import os

            if not django.apps.apps.ready:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                                      'balm.settings')
                django.setup()

            from accounts.models import CustomUser
            from django.core.mail import send_mail
            from django.conf import settings

            print(f"[INNGEST] Django configurado, buscando usuário...")

            # Busca o usuário
            try:
                @sync_to_async
                def get_user():
                    return CustomUser.objects.get(id=user_id)

                user = await get_user()

                print(f"[INNGEST] Usuário encontrado: {user.email}")
            except CustomUser.DoesNotExist:
                error_msg = f"Usuário com ID {user_id} não encontrado no banco"
                print(f"[INNGEST] ERRO: {error_msg}")
                return {"status": "error", "message": error_msg}
            except Exception as e:
                error_msg = f"Erro ao buscar usuário: {str(e)}"
                print(f"[INNGEST] ERRO: {error_msg}")
                return {"status": "error", "message": error_msg}

            # Monta a URL de verificação
            verification_url = f"{frontend_url}/verificar-email/{token}"

            # Envia o email
            try:
                print(f"[INNGEST] Preparando email para {user.email}...")

                send_mail(
                    subject='Verifique seu email - Balm',
                    message=f'''Olá {user.first_name},

                    Obrigado por se registrar na Balm!
                    
                    Para completar seu cadastro, clique no link abaixo para verificar seu email:
                    
                    {verification_url}
                    
                    Este link expira em 24 horas.
                    
                    Se você não se cadastrou em nossa plataforma, ignore este email.
                    
                    Atenciosamente,
                    Equipe Balm
                    ''',

                    html_message=f"""
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
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                print(f"[INNGEST] ✓ Email enviado com sucesso para {user.email}")
                return {
                    "status": "success",
                    "email_sent": True,
                    "recipient": user.email
                }

            except Exception as e:
                error_msg = f"Erro ao enviar email: {str(e)}"
                print(f"[INNGEST] ERRO: {error_msg}")
                traceback.print_exc()
                return {"status": "error", "message": error_msg}

        # Executa o step
        print(f"[INNGEST] Executando step de envio de email...")
        result = await ctx.step.run("sending-django-email",
                                send_email_step)

        print(f"\n{'=' * 60}")
        print(f"[INNGEST] Job concluído")
        print(f"[INNGEST] Resultado: {result}")
        print(f"{'=' * 60}\n")

        return result

    except Exception as e:
        print(f"\n{'!' * 60}")
        print(f"[INNGEST] ERRO FATAL NA FUNÇÃO")
        print(f"[INNGEST] Tipo: {type(e).__name__}")
        print(f"[INNGEST] Mensagem: {str(e)}")
        print(f"{'!' * 60}")
        traceback.print_exc()
        print(f"{'!' * 60}\n")

        # Retorna erro ao invés de re-lançar para debugging
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }