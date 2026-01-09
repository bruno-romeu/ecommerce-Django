import inngest

inngest_client = inngest.Inngest(
    app_id="inngest_functions",
)

__all__ = ['inngest_client']