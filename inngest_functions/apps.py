from django.apps import AppConfig

class EcommerceInngestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ecommerce_inngest"

    def ready(self):
        from inngest_functions import process_shipping
        from inngest_functions import send_verification_email
