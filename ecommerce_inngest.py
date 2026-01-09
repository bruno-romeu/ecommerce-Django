import inngest
import os

inngest_client = inngest.Inngest(
    app_id="inngest_functions",
    is_production=os.getenv("INNGEST_SIGNING_KEY")
)

__all__ = ['inngest_client']