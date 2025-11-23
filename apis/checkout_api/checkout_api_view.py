from rest_framework import generics, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from dotenv import load_dotenv

from apis.utils.security_logger import log_security_event
from checkout.models import Payment, Shipping, Coupon
from checkout.tasks import processar_envio_pedido
from checkout.serializer import PaymentSerializer, ShippingSerializer, CouponValidationSerializer
from orders.models import Order

import mercadopago
import os
import hmac
import hashlib
import logging
import json

from django.utils.decorators import method_decorator
from apis.decorators import ratelimit_payment, ratelimit_shipping
from django.utils import timezone

load_dotenv()

logger = logging.getLogger(__name__)

class ValidateCouponView(APIView):
    """
    View para validar cupons de desconto
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CouponValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code'].upper()
        order_total = serializer.validated_data['order_total']
        
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response(
                {'error': 'Cupom inválido'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_valid, message = coupon.is_valid(order_total)
        
        if not is_valid:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        discount_amount = coupon.calculate_discount(order_total)
        
        return Response({
            'valid': True,
            'code': coupon.code,
            'discount_percentage': float(coupon.discount_percentage),
            'discount_amount': discount_amount,
            'new_total': float(order_total) - discount_amount
        }, status=status.HTTP_200_OK)


@method_decorator(ratelimit_shipping, name='dispatch')
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
        
        # serializer.save(order=order, cost=cost, delivery_date=delivery_date)


def create_mercadopago_preference(order, client):
    mercadopago_access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    if not mercadopago_access_token:
        raise Exception("ACCESS_TOKEN do Mercado Pago não encontrado.")
    sdk = mercadopago.SDK(mercadopago_access_token)

    items = []
    for item in order.items.all():
        items.append({
            "title": item.product.name,
            "description": f"{item.quantity} x {item.product.name}",
            "quantity": item.quantity,
            "unit_price": float(item.price),
            "currency_id": "BRL",
        })

    if order.shipping_cost > 0:
        items.append({
            "title": "Frete",
            "description": "Custo de envio",
            "quantity": 1,
            "unit_price": float(order.shipping_cost),
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
            "success": f"{os.getenv('FRONTEND_URL')}/checkout/sucesso",
            "failure": f"{os.getenv('FRONTEND_URL')}/checkout/falha",
            "pending": f"{os.getenv('FRONTEND_URL')}/checkout/pendente"
        },
        "auto_return": "approved",
        "external_reference": str(order.id), 
        "notification_url": "https://balm.onrender.com/api/checkout/payments/webhook/"
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

    except Exception as e:
        print(f"ERRO DO SDK MERCADO PAGO: {e}")
        raise

    return {
        "payment_url": preference["sandbox_init_point"],
        "preference_id": preference["id"]
    }
    




@method_decorator(ratelimit_payment, name='dispatch')
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
            # Log de tentativa de acesso a pedido de outro usuário
            log_security_event(
                event_type='UNAUTHORIZED_ORDER_ACCESS',
                request=request,
                user=user,
                details=f'Tentativa de criar pagamento para pedido #{order_id} que não pertence ao usuário',
                level='error'
            )
            raise serializers.ValidationError({'order': 'Pedido não encontrado.'})

        try:
            order = Order.objects.get(id=order_id, client=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError({'order': 'Pedido não encontrado ou não pertence ao usuário.'})

        if hasattr(order, 'payment'):
            raise serializers.ValidationError({'order': 'Pagamento já realizado para este pedido.'})


        try:
            preference_dict = create_mercadopago_preference(order, user)
        except Exception as e:
            # Captura qualquer erro que a função de ajuda levantar
            return Response(
                {"error": f"Erro ao criar preferência de pagamento: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Cria o registo de Payment local
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
            'preference_id': preference_dict["preference_id"],
            'total_amount': float(order.total + order.shipping_cost)    
        }, status=status.HTTP_201_CREATED)


class PaymentWebhookView(generics.GenericAPIView):
    '''
    Webhook do Mercado Pago para receber notificações de pagamento.
    '''
    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            logger.info("=" * 50)
            logger.info(f"[WEBHOOK] Requisição recebida!")
            logger.info(f"[WEBHOOK] Body: {request.data}")
            logger.info("=" * 50)

            # Validação de assinatura
            x_signature = request.META.get('HTTP_X_SIGNATURE')
            x_request_id = request.META.get('HTTP_X_REQUEST_ID')

            logger.info("[WEBHOOK] 1️⃣ Verificando assinatura...")

            if not self._verify_webhook_signature(x_signature, x_request_id, request.body):
                logger.warning("[WEBHOOK] ⚠️ Assinatura inválida")
                return Response({"error": "Invalid signature"}, status=403)

            logger.info("[WEBHOOK] 2️⃣ Processando dados...")

            data = request.data

            # DETECTAR FORMATO
            if 'topic' in data:
                # FORMATO ANTIGO (Feed v2.0)
                topic = data.get('topic')
                payment_id = data.get('resource')

                logger.info(f"[WEBHOOK] Formato: Feed v2.0 | Topic: {topic} | ID: {payment_id}")

                if topic != 'payment':
                    logger.info(f"[WEBHOOK] ℹ️ Topic ignorado: {topic}")
                    return Response({"message": "topic ignored"}, status=200)

                action = None

            elif 'type' in data:
                # FORMATO NOVO (WebHook v1.0)
                notification_type = data.get('type')
                action = data.get('action')
                payment_id = data.get('data', {}).get('id')

                logger.info(f"[WEBHOOK] Formato: WebHook v1.0 | Type: {notification_type} | Action: {action}")

                if notification_type != 'payment':
                    logger.info(f"[WEBHOOK] ℹ️ Tipo ignorado: {notification_type}")
                    return Response({"message": "type ignored"}, status=200)

                if action == 'payment.created':
                    logger.info("[WEBHOOK] ℹ️ Pagamento criado, aguardando aprovação...")
                    return Response({"message": "payment created, waiting"}, status=200)

            else:
                logger.error("[WEBHOOK] ❌ Formato desconhecido")
                return Response({"error": "Unknown format"}, status=400)

            logger.info("[WEBHOOK] 3️⃣ Validando payment_id...")

            if not payment_id:
                logger.warning("[WEBHOOK] ⚠️ ID de pagamento não encontrado")
                return Response({"message": "payment_id not found"}, status=400)

            logger.info(f"[WEBHOOK] Payment ID: {payment_id}")

            logger.info("[WEBHOOK] 4️⃣ Buscando na API do MP...")

            sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN"))
            payment_info = sdk.payment().get(payment_id)

            logger.info(f"[WEBHOOK] Response status: {payment_info.get('status')}")

            if payment_info["status"] != 200:
                logger.error(f"[WEBHOOK] ❌ API MP erro: {payment_info}")
                return Response({"error": "MP API error"}, status=500)

            payment_data = payment_info["response"]
            status_payment = payment_data.get("status")
            external_reference = payment_data.get("external_reference")

            logger.info(f"[WEBHOOK] 5️⃣ Status: {status_payment} | Order: {external_reference}")

            if not external_reference:
                logger.warning("[WEBHOOK] ⚠️ Sem external_reference")
                return Response({"message": "no order reference"}, status=200)

            logger.info(f"[WEBHOOK] 6️⃣ Buscando Order #{external_reference}...")

            order = Order.objects.get(id=external_reference)
            logger.info(f"[WEBHOOK] Order encontrado: {order.id}")

            if not hasattr(order, 'payment'):
                logger.error(f"[WEBHOOK] ❌ Order #{order.id} sem Payment")
                return Response({"error": "Order has no payment"}, status=404)

            logger.info("[WEBHOOK] 7️⃣ Atualizando payment...")

            payment = order.payment
            old_status = payment.status
            new_status = self._map_mp_status(status_payment)

            logger.info(f"[WEBHOOK] Status: {old_status} → {new_status}")

            payment.status = new_status
            payment.transaction_id = str(payment_id)

            if status_payment == 'approved' and not payment.paid_at:
                payment.paid_at = timezone.now()

            payment.save()
            logger.info(f"[WEBHOOK] ✅ Payment salvo!")

            if status_payment == 'approved' and old_status != 'approved':
                logger.info(f"[WEBHOOK] 🚀 DISPARANDO TASK para Order #{order.id}")

                processar_envio_pedido.delay(order.id)

                log_security_event(
                    'PAYMENT_APPROVED_SHIPPING_TRIGGERED',
                    request,
                    details=f'Task disparada para Order #{order.id}',
                    level='info'
                )

            logger.info("[WEBHOOK] 8️⃣ Finalizando com sucesso")
            return Response({"message": "webhook processed successfully"}, status=200)

        except Order.DoesNotExist:
            logger.error(f"[WEBHOOK] ❌ Order não encontrado")
            return Response({"error": "Order not found"}, status=404)

        except Exception as e:
            logger.error("=" * 50)
            logger.error(f"[WEBHOOK] ❌❌❌ ERRO FATAL: {str(e)}")
            logger.error(f"[WEBHOOK] Tipo do erro: {type(e).__name__}")
            import traceback
            logger.error(f"[WEBHOOK] Traceback completo:")
            logger.error(traceback.format_exc())
            logger.error("=" * 50)
            return Response({"error": f"Internal error: {str(e)}"}, status=500)

    def _verify_webhook_signature(self, x_signature, x_request_id, body):
        return True

    def _map_mp_status(self, mp_status):
        status_map = {
            'approved': 'approved',
            'pending': 'pending',
            'in_process': 'in_process',
            'rejected': 'rejected',
            'refunded': 'refunded',
            'cancelled': 'cancelled',
        }
        return status_map.get(mp_status, 'pending')



