from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from dotenv import load_dotenv

from checkout.models import Payment, Shipping
from checkout.serializer import PaymentSerializer, ShippingSerializer
from orders.models import Order
from clients.models import Client

import mercadopago
import os

load_dotenv()

class ShippingCreateView(generics.CreateAPIView):
    queryset = Shipping.objects.all()
    serializer_class = ShippingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        order_id = self.request.data.get('order')

        try:
            order = Order.objects.get(pk=order_id, client__user = user)
        except Order.DoesNotExist:
            raise serializers.ValidationError({'order': 'Pedido não encontrado ou não pertence ao usuário.'})
        
        address = order.address

        # --- LÓGICA DE INTEGRAÇÃO COM API DE ENVIO ---
        #
        #
        #
        #
        #
        # 
        #
        #
        #
        #
        #
        # serializer.save(order=order, cost=cost, delivery_date=delivery_date)


def create_mercadopago_preference(order, client):
    api_key = os.getenv("Access_Token")
    sdk = mercadopago.SDK(api_key)

    items = [{
        "title": f"Pedido #{order.id}",
        "description": "Descrição do pedido",
        "quantity": 1,
        "unit_price": float(order.total),
        "currency_id": "BRL",
    }]

    payer = {
        "name": client.name,
        "email": client.email,
    }

    preference_data = {
        "items": items,
        "payer": payer,
        "notification_url": "https://SEU_DOMINIO.com/api/checkout/payments/webhook/"
        # adicionar back_url
    }

    response = sdk.preference().create(preference_data)
    return {
        "payment_url": response["response"]["init_point"],
        "payment_id": response["response"]["id"]
    }


class PaymentCreateView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        order = serializer.validated_data.get('order')

        try:
            order = Order.objects.get(pk=order.id, client__user=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError({'order': 'Pedido não encontrado ou não pertence ao usuário.'})
        
        if hasattr(order, 'payment'):
            raise serializers.ValidationError({'order': 'Pagamento já realizado para este pedido.'})
        
        # --- LÓGICA DE INTEGRAÇÃO COM O MERCADO PAGO ---

        client = Client.objects.get(user=user)

        try:
            preference = create_mercadopago_preference(order, client)
        except Exception as e:
            return Response(
                {"error": "Erro ao criar preferência de pagamento com o Mercado Pago."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        payment = serializer.save(
            order=order,
            status='pending',
            amount=order.total,
            transaction_id=preference["payment_id"],
            method=self.request.data.get('method')
        )

        return Response({
            'payment_id_local': payment.id,
            'payment_url': preference["payment_url"],
            'qr_code': preference["payment_url"],  # verificar como o QR code é retornado
        }, status=status.HTTP_201_CREATED)


class PaymentWebhookView(generics.GenericAPIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        # --- LÓGICA DE RECEBIMENTO DE WEBHOOK DO MERCADO PAGO ---


        data = request.data
        if 'resource' in data and 'topic' in data and data['topic'] == 'merchant_order':
            merchant_order_id = data['resource'].split('/')[-1]
