from rest_framework import serializers
from .models import Category, Size, Essence, Product

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

