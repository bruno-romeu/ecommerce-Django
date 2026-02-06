from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone

from apis.utils.security_logger import log_security_event
from checkout.utils import gerar_etiqueta_melhor_envio
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    autocomplete_fields = ('product', )
    readonly_fields = ('price',)
    fields = ('product', 'quantity', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_form_template = 'admin/orders/order/change_form.html'
    list_display = ('id', 'client', 'status', 'get_items_total', 'shipping_cost', 'total', 'created_at', 'payment_status', 'shipping_status')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'client__user__username')
    inlines = [OrderItemInline] # Adiciona os itens do pedido na mesma página do admin
    readonly_fields = ('total', 'created_at', 'payment_status', 'shipping_status', 'client', 'address') 
    actions = ['mark_as_paid', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_canceled']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/generate-shipping/',
                self.admin_site.admin_view(self.generate_shipping_label),
                name='orders_order_generate_shipping'
            )
        ]
        return custom_urls + urls

    def generate_shipping_label(self, request, object_id):
        order = self.get_object(request, object_id)

        if not order:
            self.message_user(request, 'Pedido não encontrado.', level=messages.ERROR)
            return redirect('admin:orders_order_changelist')

        if order.status != 'processing':
            self.message_user(
                request,
                'O pedido precisa estar em "Em Separação" para gerar a etiqueta.',
                level=messages.WARNING
            )
            return redirect('admin:orders_order_change', object_id)

        shipping = getattr(order, 'shipping', None)
        if not shipping:
            self.message_user(request, 'Pedido sem envio vinculado.', level=messages.ERROR)
            return redirect('admin:orders_order_change', object_id)

        if shipping.label_url:
            self.message_user(request, 'Etiqueta já foi gerada para este pedido.', level=messages.INFO)
            return redirect('admin:orders_order_change', object_id)

        try:
            shipping.status = 'processing'
            shipping.retry_count += 1
            shipping.error_message = None
            shipping.save(update_fields=['status', 'retry_count', 'error_message', 'updated_at'])

            resultado = gerar_etiqueta_melhor_envio(order)

            shipping.tracking_code = resultado['tracking_code']
            shipping.label_url = resultado['label_url']
            shipping.melhor_envio_order_id = resultado.get('melhor_envio_id')
            shipping.label_generated_at = timezone.now()
            shipping.status = 'shipped'
            shipping.error_message = None
            shipping.save(update_fields=[
                'tracking_code',
                'label_url',
                'melhor_envio_order_id',
                'label_generated_at',
                'status',
                'error_message',
                'updated_at'
            ])

            order.status = 'shipped'
            order.save(update_fields=['status'])

            log_security_event(
                'MANUAL_SHIPPING_LABEL_GENERATED',
                request,
                user=request.user,
                details=f'Etiqueta gerada manualmente para pedido #{order.id}',
                level='info'
            )

            self.message_user(
                request,
                'Etiqueta gerada com sucesso e pedido marcado como enviado.',
                level=messages.SUCCESS
            )
        except Exception as e:
            shipping.status = 'failed'
            shipping.error_message = str(e)
            shipping.save(update_fields=['status', 'error_message', 'updated_at'])

            self.message_user(
                request,
                f'Erro ao gerar etiqueta: {str(e)}',
                level=messages.ERROR
            )

        return redirect('admin:orders_order_change', object_id)

    def mark_as_paid(self, request, queryset):
        queryset.filter(status='pending').update(status='paid')
    mark_as_paid.short_description = "Marcar pedidos selecionados como pagos"
    
    def mark_as_shipped(self, request, queryset):
        queryset.filter(status='processing').update(status='shipped')
    mark_as_shipped.short_description = "Marcar pedidos selecionados como enviados"

    def mark_as_processing(self, request, queryset):
        queryset.filter(status='paid').update(status='processing')
    mark_as_processing.short_description = "Marcar pedidos selecionados como em separação"

    def mark_as_delivered(self, request, queryset):
        queryset.filter(status='shipped').update(status='delivered')
    mark_as_delivered.short_description = "Marcar pedidos selecionados como entregues"

    def mark_as_canceled(self, request, queryset):
        queryset.filter(status__in=['pending', 'paid', 'processing']).update(status='canceled')
    mark_as_canceled.short_description = "Marcar pedidos selecionados como cancelados"

    def get_items_total(self, obj):
        """Total só dos produtos"""
        return sum(item.price * item.quantity for item in obj.items.all())
    get_items_total.short_description = 'Total Produtos'
