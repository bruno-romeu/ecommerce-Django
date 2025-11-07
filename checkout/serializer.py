from rest_framework import serializers
from .models import Shipping, Payment, Coupon
from accounts.models import Address

from orders.models import Order


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_percentage']


class CouponValidationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    order_total = serializers.DecimalField(max_digits=10, decimal_places=2)

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class ShippingSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    class Meta:
        model = Shipping
        fields = '__all__'
        read_only_fields = ['cost', 'delivery_date', 'status']

class PaymentSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('status', 'transaction_id', 'paid_at')
