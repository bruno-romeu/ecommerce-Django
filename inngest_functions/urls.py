from django.urls import path
import inngest.django
from ecommerce_inngest import inngest_client
from .send_verification_email import send_verification_email_fn
from .process_shipping import process_shipping_fn

inngest.django.serve(
    inngest_client, 
    [send_verification_email_fn, process_shipping_fn]
)

urlpatterns = inngest.django.urls 