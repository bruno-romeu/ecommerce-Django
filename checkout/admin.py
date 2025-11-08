from django.contrib import admin
from .models import Shipping, Payment, Coupon
from accounts.models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'street', 'number', 'city', 'state', 'zipcode',)
    search_fields = ('client__name', 'street', 'city', 'state',)
    list_filter = ('state',)

@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = ('order', 'get_address', 'status', 'tracking_code',)
    search_fields = ('order__id', 'tracking_code',)
    list_filter = ('status',)

    def get_address(self, obj):
        return obj.order.address if obj.order else 'N/A'
    get_address.short_description = 'Endereço de Entrega'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'get_amount', 'status', 'method')
    search_fields = ('order__id', 'method')
    list_filter = ('status',)

    def get_amount(self, obj):
        return obj.order.total if obj.order else 'N/A'
    get_amount.short_description = 'Valor do Pagamento'

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'is_active','valid_from', 'valid_until', 'usage_limit', 'times_used', 'minimum_purchase','created_at')
    search_fields = ('code',)
    list_filter = ('is_active', 'valid_from', 'valid_until')
