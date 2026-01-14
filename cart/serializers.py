from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Essence, Product
from products.serializers import ProductSerializer, EssenceSerializer

class CartItemSerializer(serializers.ModelSerializer):

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    product = ProductSerializer(read_only=True)
    essence_id = serializers.PrimaryKeyRelatedField(
        queryset=Essence.objects.filter(is_active=True),
        source='essence',
        write_only=True,
        required=False,
        allow_null=True
    )
    essence = EssenceSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = '__all__'
        read_only_fields = ('cart', 'product', 'essence', 'price')

    
    def validate(self, data):
        """
        Validação cruzada: Verifica se a essência escolhida pertence 
        à categoria do produto selecionado.
        """
        product = data.get('product')
        essence = data.get('essence')

        product_category_essences = product.category.essences.all() if product.category else []

        if product_category_essences.exists():
            if not essence:
                raise serializers.ValidationError({
                    "essence_id": "Este produto requer a seleção de uma essência."
                })
            
            if essence not in product_category_essences:
                raise serializers.ValidationError({
                    "essence_id": f"A essência '{essence.name}' não está disponível para o produto '{product.name}'."
                })
        
        else:
            if essence:
                raise serializers.ValidationError({
                    "essence_id": "Este produto não aceita essências."
                })

        return data



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