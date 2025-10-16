from django.urls import path
from .site_config_api_view import HeroSectionActivateView, HeroSectionDetailUpdateDestroyView, HeroSectionListCreateView, HeroSectionPublicView

urlpatterns = [
    path('api/hero/', HeroSectionPublicView.as_view(), name='hero-public'),
    
    path('api/admin/hero/', HeroSectionListCreateView.as_view(), name='hero-list-create'),
    path('api/admin/hero/<int:pk>/', HeroSectionDetailUpdateDestroyView.as_view(), name='hero-detail'),
    path('api/admin/hero/<int:pk>/activate/', HeroSectionActivateView.as_view(), name='hero-activate'),
]