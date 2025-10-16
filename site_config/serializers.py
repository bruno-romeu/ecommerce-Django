from rest_framework import serializers
from .models import HeroSection

class HeroSectionPublicSerializer(serializers.ModelSerializer):
    background_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = HeroSection
        fields = ['id', 'title', 'subtitle', 'button_text', 'button_link', 'background_image_url']
    
    def get_background_image_url(self, obj):
        request = self.context.get('request')
        if obj.background_image and request:
            return request.build_absolute_uri(obj.background_image.url)
        return obj.background_image.url if obj.background_image else None

class HeroSectionAdminSerializer(serializers.ModelSerializer):
    background_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = HeroSection
        fields = ['id', 'title', 'subtitle', 'button_text', 'button_link', 'background_image', 'background_image_url', 'is_active']
    
    def get_background_image_url(self, obj):
        request = self.context.get('request')
        if obj.background_image and request:
            return request.build_absolute_uri(obj.background_image.url)
        return obj.background_image.url if obj.background_image else None