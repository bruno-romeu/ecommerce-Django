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
            "success": f"{os.getenv("FRONTEND_URL")}/checkout/sucesso",
            "failure": f"{os.getenv("FRONTEND_URL")}/checkout/falha",
            "pending": f"{os.getenv("FRONTEND_URL")}/checkout/pendente"
        },
        "auto_return": "approved",
        "external_reference": str(order.id), 
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
    permission_classes = []

    def post(self, request, *args, **kwargs):
        # --- LÓGICA DE RECEBIMENTO DE WEBHOOK DO MERCADO PAGO ---
        x_signature = request.META.get('HTTP_X_SIGNATURE')
        x_request_id = request.META.get('HTTP_X_REQUEST_ID')
        logger.info(f"[WEBHOOK] Recebido do Mercado Pago: {request.data}")

        if not self.verify_webhook_signature(x_signature, x_request_id, request.body):
            log_security_event(
                'WEBHOOK_INVALID_SIGNATURE',
                request,
                details='Tentativa de webhook com assinatura inválida'
            )
            logger.warning("[WEBHOOK] Assinatura inválida")
            return Response({"error": "Invalid signature"}, status=403)
        
        data = request.data
        notification_type = data.get('type')

        if notification_type == 'payment':
            payment_id = data.get('data', {}).get('id')
            
            if not payment_id:
                logger.warning("[WEBHOOK] ⚠️ ID de pagamento não encontrado")
                return Response({"message": "payment_id not found"}, status=400)
            
            logger.info(f"[WEBHOOK] Processando pagamento ID: {payment_id}")

            try:
                sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN"))
                payment_info = sdk.payment().get(payment_id)
                
                if payment_info["status"] != 200:
                    logger.error(f"[WEBHOOK] ❌ Erro ao buscar pagamento: {payment_info}")
                    return Response({"error": "Failed to get payment info"}, status=500)
                
                payment_data = payment_info["response"]

                status_payment = payment_data.get("status")
                external_reference = payment_data.get("external_reference")  
                transaction_amount = payment_data.get("transaction_amount")
                
                logger.info(f"[WEBHOOK] Status: {status_payment} | Order: {external_reference}")


                try:
                        payment = Payment.objects.get(transaction_id=external_reference)
                        old_status = payment.status
                        payment.status = self._map_mp_status(status_payment)
                        
                        if status_payment == 'approved' and not payment.paid_at:
                            payment.paid_at = timezone.now()
                        
                        payment.save()
                        
                        logger.info(f"[WEBHOOK] ✅ Payment atualizado: {old_status} → {payment.status}")
                        
                        if status_payment == 'approved' and old_status != 'approved':
                            order = payment.order
                            
                            logger.info(f"[WEBHOOK] 🚀 Disparando task de envio para Order #{order.id}")
                            
                            processar_envio_pedido.delay(order.id)
                            
                            log_security_event(
                                'PAYMENT_APPROVED_SHIPPING_TRIGGERED',
                                request,
                                details=f'Pagamento aprovado. Task de envio disparada para Order #{order.id}',
                                level='info'
                            )
                except Payment.DoesNotExist:
                    logger.error(f"[WEBHOOK] ❌ Payment não encontrado: {external_reference}")
                    return Response({"error": "Payment not found"}, status=404)
                
                return Response({"message": "webhook processed"}, status=200)
            
            except Exception as e:
                logger.error(f"[WEBHOOK] ❌ Erro ao processar: {str(e)}")
                return Response({"error": str(e)}, status=500)
    
        logger.info(f"[WEBHOOK] Tipo de notificação ignorado: {notification_type}")
        return Response({"message": "ignored"}, status=200)
    

    def _verify_webhook_signature(self, x_signature, x_request_id, body):
        """
        Valida a assinatura do webhook do Mercado Pago.
        
        Documentação: https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks
        """
        # TODO: Implementar validação de assinatura
        # Por enquanto, retorna True (em produção, DEVE implementar)
        
        # Exemplo de implementação:
        # secret = os.getenv("MERCADOPAGO_WEBHOOK_SECRET")
        # if not secret:
        #     return True  # Se não tiver secret configurado, aceita
        # 
        # expected_signature = hmac.new(
        #     secret.encode(),
        #     body,
        #     hashlib.sha256
        # ).hexdigest()
        # 
        # return hmac.compare_digest(expected_signature, x_signature)
        
        return True  # ⚠️ TEMPORÁRIO - Implementar validação em produção
    
    def _map_mp_status(self, mp_status):
        """
        Mapeia status do Mercado Pago para nosso modelo.
        
        Status do MP:
        - approved: Pagamento aprovado
        - pending: Aguardando pagamento
        - in_process: Em processamento
        - rejected: Rejeitado
        - refunded: Reembolsado
        - cancelled: Cancelado
        """
        status_map = {
            'approved': 'approved',
            'pending': 'pending',
            'in_process': 'in_process',
            'rejected': 'rejected',
            'refunded': 'refunded',
            'cancelled': 'cancelled',
        }
        return status_map.get(mp_status, 'pending')



