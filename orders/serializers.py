from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer
from accounts.models import Address
from decimal import Decimal

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'customization_details']
        read_only_fields = ['id', 'product', 'price', 'customization_details']


class ShippingDetailSerializer(serializers.Serializer):
    """Serializer para dados de envio (leitura apenas)"""
    id = serializers.IntegerField()
    tracking_code = serializers.CharField(required=False, allow_null=True)
    carrier = serializers.CharField(required=False, allow_null=True)
    estimated_delivery = serializers.DateField(required=False, allow_null=True)
    status = serializers.CharField()
    cost = serializers.DecimalField(max_digits=8, decimal_places=2)


class PaymentDetailSerializer(serializers.Serializer):
    """Serializer para dados de pagamento (leitura apenas)"""
    id = serializers.IntegerField()
    method = serializers.CharField()
    status = serializers.CharField()
    paid_at = serializers.DateTimeField(required=False, allow_null=True)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    total_with_shipping = serializers.SerializerMethodField()

    address = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        write_only=True  
    )

    shipping_cost = serializers.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        required=False,
        default=0.00
    )

    shipping_service = serializers.CharField(required=False, allow_blank=True)
    shipping_carrier = serializers.CharField(required=False, allow_blank=True)
    estimated_delivery_days = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Order
        fields = ['id', 'address', 'status', 'total', 'shipping_cost', 
            'total_with_shipping', 'created_at', 'items', 'shipping', 
            'payment', 'shipping_service', 'shipping_carrier', 
            'estimated_delivery_days']
        read_only_fields = ['id', 'total', 'created_at', 'items', 'shipping', 'payment', 'total_with_shipping']

    def create(self, validated_data):
        validated_data.pop('shipping_service', None)
        validated_data.pop('shipping_carrier', None)
        validated_data.pop('estimated_delivery_days', None)
        return super().create(validated_data)

    def get_total_with_shipping(self, obj):
        """Retorna total + frete"""
        total = obj.total if obj.total else Decimal('0.00')
        shipping = obj.shipping_cost if obj.shipping_cost else Decimal('0.00')
        return float(total + shipping)

    def get_shipping(self, obj):
        """Retorna dados de envio se existirem"""
        if hasattr(obj, 'shipping') and obj.shipping:
            return {
                'id': obj.shipping.id,
                'tracking_code': obj.shipping.tracking_code,
                'carrier': obj.shipping.carrier,
                'estimated_delivery': obj.shipping.estimated_delivery,
                'status': obj.shipping.status,
                'cost': float(obj.shipping.cost),
            }
        return None

    def get_payment(self, obj):
        """Retorna dados de pagamento se existirem"""
        if hasattr(obj, 'payment') and obj.payment:
            return {
                'id': obj.payment.id,
                'method': obj.payment.method,
                'status': obj.payment.status,
                'paid_at': obj.payment.paid_at,
            }
        return None
    
    def validate_address(self, value):
        """Garante que o endereço pertence ao usuário logado"""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError(
                "Este endereço não pertence a você."
            )
        return value


class OrderStatusSerializer(serializers.ModelSerializer):
    """Serializer para atualizar apenas o status do pedido"""
    
    class Meta:
        model = Order
        fields = ['status']
    
    def validate_status(self, value):
        current_status = self.instance.status
        
        valid_transitions = {
            'pending': ['paid', 'processing', 'canceled'],
            'paid': ['processing', 'canceled'],
            'processing': ['shipped', 'canceled'],
            'shipped': ['delivered'],
            'delivered': [],
            'canceled': [],
        }
        
        if value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Não é possível mudar de '{current_status}' para '{value}'"
            )
        
        return value