from django.apps import AppConfig

class InngestFunctionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inngest_functions"

    def ready(self):
        try:
            from . import process_shipping
            from . import send_verification_email
            print("[INNGEST] ✓ Funções registradas com sucesso")
        except Exception as e:
            print(f"[INNGEST] ✗ Erro ao registrar funções: {e}")