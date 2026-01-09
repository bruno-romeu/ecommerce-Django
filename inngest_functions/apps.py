from django.apps import AppConfig

class EcommerceInngestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ecommerce_inngest"

    def ready(self):
        import process_shipping
        import send_verification_email
