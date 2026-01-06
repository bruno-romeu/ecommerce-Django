import inngest

inngest_client = inngest.Inngest(
    app_id="ecommerce_app",
    is_production=False,
)

__all__ = ['inngest_client']