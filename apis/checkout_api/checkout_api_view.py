from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from dotenv import load_dotenv

from checkout.models import Payment, Shipping
from checkout.serializer import PaymentSerializer, ShippingSerializer
from orders.models import Order
from orders.serializers import OrderSerializer
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
    access_token = os.getenv("ACCESS_TOKEN")
    sdk = mercadopago.SDK(access_token)

    items = []
    for item in order.items.all():
        items.append({
            "title": item.product.name,
            "description": f"{item.quantity} x {item.product.name}",
            "quantity": item.quantity,
            "unit_price": float(item.price),
            "currency_id": "BRL",
        })

    payer = {
        "name": f"{client.user.first_name} {client.user.last_name}",
        "email": client.user.email,
    }

    preference_data = {
        "items": items,
        "payer": payer,
        "back_urls": {
            "success": "https://bruno-romeu.github.io/portfolio/",
            "failure": "https://bruno-romeu.github.io/portfolio/#projetos",
            "pending": "https://bruno-romeu.github.io/portfolio/projetos/revenda.html"
        },
        "auto_return": "approved",
        "notification_url": "https://bruno-romeu.github.io/portfolio/index.html"
    }

    try:
        response = sdk.preference().create(preference_data)
    except Exception as e:
        return Response(
            {"error": f"Erro ao criar preferência de pagamento com o Mercado Pago: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return {
        "payment_url": response["response"]["init_point"],
        "payment_id": response["response"]["id"]
    }


class PaymentCreateView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        order_id = request.data.get('order')

        try:
            order = Order.objects.get(pk=order_id, client__user=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError({'order': 'Pedido não encontrado ou não pertence ao usuário.'})

        if hasattr(order, 'payment'):
            raise serializers.ValidationError({'order': 'Pagamento já realizado para este pedido.'})

        client = Client.objects.get(user=user)

        try:
            preference = create_mercadopago_preference(order, client)
        except Exception as e:
            return Response(
                {"error": "Erro ao criar preferência de pagamento com o Mercado Pago."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        payment = Payment.objects.create(
            order=order,
            status='pending',
            transaction_id=preference["payment_id"],
            method="MERCADOPAGO"
        )

        return Response({
            'payment_id_local': payment.id,
            'payment_url': preference["payment_url"],
        }, status=status.HTTP_201_CREATED)

class PaymentWebhookView(generics.GenericAPIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        # --- LÓGICA DE RECEBIMENTO DE WEBHOOK DO MERCADO PAGO ---

        data = request.data
        if "id" in data and "type" in data and data["type"] == "payment":
            payment_id = data["id"]
            sdk = mercadopago.SDK(os.getenv("ACCESS_TOKEN"))
            payment_info = sdk.payment().get(payment_id)

            status_payment = payment_info["response"]["status"]

            Payment.objects.filter(transaction_id=str(payment_id)).update(status=status_payment)


            return Response({"message": "ok"}, status=200)
        return Response({"message": "ignored"}, status=200)

