from celery import shared_task
from django.utils import timezone
from orders.models import Order
from checkout.models import Shipping
from .utils import gerar_etiqueta_melhor_envio
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def processar_envio_pedido(self, order_id):
    """
    Task principal: Gera etiqueta de envio após pagamento aprovado.
    
    Args:
        order_id: ID do pedido
        
    Returns:
        dict: Resultado da operação
    """
    try:
        order = Order.objects.select_related('shipping', 'payment', 'address').get(id=order_id)
        logger.info(f"[TASK] Processando envio para pedido #{order.id}")
        
        if not hasattr(order, 'shipping'):
            logger.error(f"[TASK] Pedido #{order.id} não tem registro de Shipping")
            return {'success': False, 'error': 'Shipping não encontrado'}
        
        shipping = order.shipping
        
        if shipping.label_url:
            logger.warning(f"[TASK] Etiqueta já foi gerada para pedido #{order.id}")
            return {'success': True, 'message': 'Etiqueta já existe', 'tracking_code': shipping.tracking_code}
        
        shipping.status = 'processing'
        shipping.retry_count += 1
        shipping.save()
        
        logger.info(f"[TASK] Chamando API Melhor Envio para pedido #{order.id}")
        resultado = gerar_etiqueta_melhor_envio(order)
        
        shipping.tracking_code = resultado['tracking_code']
        shipping.label_url = resultado['label_url']
        shipping.melhor_envio_order_id = resultado.get('melhor_envio_id')
        shipping.label_generated_at = timezone.now()
        shipping.status = 'shipped'
        shipping.error_message = None
        shipping.save()
        
        order.status = 'shipped'
        order.save()
        
        logger.info(f"[TASK] ✅ Etiqueta gerada com sucesso para pedido #{order.id}")
        logger.info(f"[TASK] Tracking code: {shipping.tracking_code}")
        
        # (configurar futuramente) Disparar task de email
        # notificar_cliente_email.delay(order_id)
        
        return {
            'success': True,
            'order_id': order.id,
            'tracking_code': shipping.tracking_code,
            'label_url': shipping.label_url
        }
        
    except Order.DoesNotExist:
        logger.error(f"[TASK] ❌ Pedido #{order_id} não encontrado")
        return {'success': False, 'error': 'Pedido não encontrado'}
        
    except Exception as e:
        logger.error(f"[TASK] ❌ Erro ao processar envio para pedido #{order_id}: {str(e)}")
        
        try:
            shipping.status = 'failed'
            shipping.error_message = str(e)
            shipping.save()
        except:
            pass
        
        # Tentar novamente em 5 minutos (300 segundos)
        # Retry automático até 3 vezes
        raise self.retry(exc=e, countdown=300)


@shared_task
def notificar_cliente_email(order_id):
    """
    Task secundária: Envia email ao cliente com código de rastreio.
    
    Args:
        order_id: ID do pedido
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        order = Order.objects.select_related('shipping', 'client').get(id=order_id)
        shipping = order.shipping
        
        if not shipping.tracking_code:
            logger.warning(f"[EMAIL] Pedido #{order_id} sem tracking code")
            return
        
        subject = f"Seu pedido #{order.id} foi enviado! 📦"
        message = f"""
        Olá {order.client.first_name}!
        
        Seu pedido #{order.id} foi enviado e está a caminho! 🚚
        
        Código de rastreio: {shipping.tracking_code}
        Transportadora: {shipping.carrier}
        Previsão de entrega: {shipping.estimated_delivery}
        
        Você pode acompanhar seu pedido através do link:
        {shipping.label_url}
        
        Obrigado por comprar conosco!
        Equipe Balm
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.client.email],
            fail_silently=False,
        )
        
        logger.info(f"[EMAIL] ✅ Email enviado para {order.client.email}")
        return {'success': True, 'email': order.client.email}
        
    except Order.DoesNotExist:
        logger.error(f"[EMAIL] ❌ Pedido #{order_id} não encontrado")
        return {'success': False, 'error': 'Pedido não encontrado'}
        
    except Exception as e:
        logger.error(f"[EMAIL] ❌ Erro ao enviar email para pedido #{order_id}: {str(e)}")
        return {'success': False, 'error': str(e)}