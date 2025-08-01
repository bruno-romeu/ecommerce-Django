from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    autocomplete_fields = ('product', )
    readonly_fields = ('price',)
    fields = ('product', 'quantity', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'status', 'total', 'created_at', 'payment_status', 'shipping_status')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'client__user__username')
    inlines = [OrderItemInline] # Adiciona os itens do pedido na mesma página do admin
    readonly_fields = ('total', 'created_at', 'payment_status', 'shipping_status', 'client', 'address') 
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_canceled']

    def mark_as_paid(self, request, queryset):
        queryset.filter(status='pending').update(status='paid')
    mark_as_paid.short_description = "Marcar pedidos selecionados como pagos"
    
    def mark_as_shipped(self, request, queryset):
        queryset.filter(status='paid').update(status='shipped')
    mark_as_shipped.short_description = "Marcar pedidos selecionados como enviados"

    def mark_as_delivered(self, request, queryset):
        queryset.filter(status='shipped').update(status='delivered')
    mark_as_delivered.short_description = "Marcar pedidos selecionados como entregues"

    def mark_as_canceled(self, request, queryset):
        queryset.filter(status__in=['pending', 'paid']).update(status='canceled')
    mark_as_canceled.short_description = "Marcar pedidos selecionados como cancelados"
