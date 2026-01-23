from rest_framework import serializers
from .models import Category, Size, Essence, Product, ProductCustomization

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'

    def get_image(self, category):
        request = self.context.get('request')
        if category.image:
            return request.build_absolute_uri(category.image.url)
        return None

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'

class EssenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Essence
        fields = '__all__'

    def get_image_url(self, essence):
        if essence.image:
            return self.context['request'].build_absolute_uri(essence.image.url)
        return None

class ProductCustomizationSerializer(serializers.ModelSerializer):
    available_options = serializers.SerializerMethodField()

    class Meta:
        model = ProductCustomization
        fields = [
            'id', 'name', 'instruction', 'input_type',
            'available_options', 'price_extra', 'free_above_quantity'
        ]

    def get_available_options(self, obj):
        """Transforma 'Azul,Vermelho' em ['Azul', 'Vermelho'] para o front"""
        if obj.available_options:
            return [opt.strip() for opt in obj.available_options.split(',')]
        return []

class ProductSerializer(serializers.ModelSerializer):

    image = serializers.SerializerMethodField()
    category = serializers.StringRelatedField()
    size = SizeSerializer(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def get_image(self, product):
        if product.image:
            request = self.context['request']
            return request.build_absolute_uri(product.image.url)
        return None

