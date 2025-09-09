from rest_framework import serializers
from .models import Shipping, Payment
from accounts.models import Address

from orders.models import Order

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
