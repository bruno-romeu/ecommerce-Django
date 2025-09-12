from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer
from accounts.models import Address

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']
        read_only_fields = ['price']

class OrderSerializer(serializers.ModelSerializer):
    address = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all()
    )
    class Meta:
        model = Order
        fields = ['id', 'address']
        read_only_fields = ['id', 'client', 'address', 'status', 'items', 'total_value', 'created_at']

    def get_total_value(self, obj):
        return sum(item.price * item.quantity for item in obj.items.all())


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

