from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from dotenv import load_dotenv

from checkout.models import Payment, Shipping
from checkout.serializer import PaymentSerializer, ShippingSerializer
from orders.models import Order
from orders.serializers import OrderSerializer
from accounts.models import CustomUser

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
    if not access_token:
        raise Exception("ACCESS_TOKEN do Mercado Pago não encontrado.")
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
        "name": f"{client.first_name}",
        "surname": f"{client.last_name}",
        "email": client.email,
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
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
    except Exception as e:
        print(f"ERRO DO SDK MERCADO PAGO: {e}")
        raise # Levanta o erro para a view tratar

    return {
        "payment_url": preference["init_point"],
        "preference_id": preference["id"]
    }


class PaymentCreateView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        order_id = request.data.get('order')

        try:
            order = Order.objects.get(id=order_id, client=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError({'order': 'Pedido não encontrado ou não pertence ao usuário.'})

        if hasattr(order, 'payment'):
            raise serializers.ValidationError({'order': 'Pagamento já realizado para este pedido.'})


        try:
            # Chama a nossa função de ajuda
            preference_dict = create_mercadopago_preference(order, user)
        except Exception as e:
            # Captura qualquer erro que a função de ajuda levantar
            return Response(
                {"error": f"Erro ao criar preferência de pagamento: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Cria o nosso registo de Payment local
        payment = Payment.objects.create(
            order=order,
            status='pending',
            # Guardamos o ID da preferência para referência futura
            transaction_id=preference_dict["preference_id"], 
            method="MERCADOPAGO"
        )

        # A view constrói a Response final para o front-end
        return Response({
            'payment_id_local': payment.id,
            'payment_url': preference_dict["payment_url"],
            'preference_id': preference_dict["preference_id"]
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

