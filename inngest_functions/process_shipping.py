from __future__ import annotations
import traceback
import logging
from asgiref.sync import sync_to_async
from inngest import Context, TriggerEvent
from typing import TYPE_CHECKING
from ecommerce_inngest import inngest_client

if TYPE_CHECKING:
    from orders.models import Order

logger = logging.getLogger(__name__)




def get_order_with_items(order_id):
    from orders.models import Order
    return (
        Order.objects
        .select_related('address', 'client', 'shipping', 'payment')
        .prefetch_related('items__product__size')
        .get(id=order_id)
    )


def mark_shipping_processing(order_id):
    from orders.models import Order
    order = Order.objects.select_related('shipping').get(id=order_id)
    shipping = order.shipping

    shipping.status = "processing"
    shipping.retry_count += 1
    shipping.save()

    return shipping.retry_count


def save_shipping_success(order_id, resultado):
    from orders.models import Order
    from django.utils import timezone

    order = Order.objects.select_related('shipping').get(id=order_id)
    shipping = order.shipping

    shipping.tracking_code = resultado["tracking_code"]
    shipping.label_url = resultado["label_url"]
    shipping.melhor_envio_order_id = resultado.get("melhor_envio_id")
    shipping.label_generated_at = timezone.now()
    shipping.status = "shipped"
    shipping.error_message = None
    shipping.save()

    order.status = "shipped"
    order.save()


@inngest_client.create_function(
    fn_id="process-shipping-after-payment",
    trigger=TriggerEvent(event="payment/approved"),
    retries=3,
)
async def process_shipping_fn(ctx: Context):
    from orders.models import Order

    data = ctx.event.data
    order_id = data.get("order_id")
    payment_id = data.get("payment_id")

    if not order_id:
        raise ValueError("order_id é obrigatório no evento")

    logger.info(f"[INNGEST SHIPPING] Iniciando envio | order={order_id}")

    try:

        async def validate_order_step():
            order = await sync_to_async(get_order_with_items)(order_id)

            shipping = order.shipping

            if shipping.label_url:
                return {
                    "status": "already_processed",
                    "tracking_code": shipping.tracking_code,
                    "label_url": shipping.label_url
                }

            return {"status": "ok"}

        validation = await ctx.step.run("validate-order", validate_order_step)

        if validation["status"] == "already_processed":
            logger.info(f"[INNGEST SHIPPING] Etiqueta já existe | order={order_id}")
            return validation


        await ctx.step.run(
            "mark-processing",
            lambda: sync_to_async(mark_shipping_processing)(order_id)
        )


        async def generate_label_step():
            from checkout.utils import gerar_etiqueta_melhor_envio

            order = await sync_to_async(get_order_with_items)(order_id)
            return gerar_etiqueta_melhor_envio(order)

        resultado = await ctx.step.run(
            "generate-shipping-label",
            generate_label_step
        )


        await ctx.step.run(
            "save-shipping",
            lambda: sync_to_async(save_shipping_success)(order_id, resultado)
        )

        logger.info(
            f"[INNGEST SHIPPING] ✅ Envio concluído | order={order_id} | tracking={resultado.get('tracking_code')}"
        )

        return {
            "status": "success",
            "order_id": order_id,
            **resultado
        }

    except Exception as e:
        logger.error(
            f"[INNGEST SHIPPING] ❌ ERRO | order={order_id} | {str(e)}"
        )
        traceback.print_exc()
        raise
