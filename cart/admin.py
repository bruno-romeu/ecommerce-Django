from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    autocomplete_fields = ('product',)
    readonly_fields = ('product', 'quantity',)
    fields = ('product', 'quantity',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'get_total',)
    list_filter = ('user', 'created_at',)
    search_fields = ('user__username', 'created_at',)
    inlines = [CartItemInline]
    readonly_fields = ('user', 'created_at', 'get_total',)

    def get_total(self, obj):
        return obj.get_total()
    get_total.short_description = 'Valor Total'
    


