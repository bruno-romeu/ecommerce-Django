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

    category = CategorySerializer(read_only=True)
    size = SizeSerializer(read_only=True)
    essence = EssenceSerializer(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
