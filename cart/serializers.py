from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product
from products.serializers import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    product = ProductSerializer(read_only=True)
    class Meta:
        model = CartItem
        fields = '__all__'
        read_only_fields = ('cart', 'product', 'price')





class CartSerializer(serializers.ModelSerializer):
    # Many=True porque um carrinho pode ter múltiplos itens.
    items = CartItemSerializer(many=True, read_only=True)
    total_value = serializers.SerializerMethodField()
    class Meta:
        model = Cart
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'items', 'total_value')

    def get_total_value(self,obj):
        return obj.get_total()