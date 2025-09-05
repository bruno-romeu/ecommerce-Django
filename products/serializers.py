from rest_framework import serializers
from .models import Category, Size, Essence, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'

class EssenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Essence
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):

    image = serializers.SerializerMethodField()
    category = serializers.StringRelatedField()
    size = serializers.PrimaryKeyRelatedField(queryset=Size.objects.all(), allow_null=True)
    essence = serializers.PrimaryKeyRelatedField(queryset=Essence.objects.all(), allow_null=True)

    class Meta:
        model = Product
        fields = '__all__'

    def get_image(self, product):
        request = self.context.get('request')
        if product.image:
            return request.build_absolute_uri(product.image.url)
        
        return None

