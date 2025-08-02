from django.urls import path
from .checkout_api_view import ShippingCreateView, PaymentCreateView, PaymentWebhookView

urlpatterns = [
    path('shipping/create/', ShippingCreateView.as_view(), name='shipping,create'),

    path('payments/create/', PaymentCreateView.as_view(), name='payment-create'),

    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]