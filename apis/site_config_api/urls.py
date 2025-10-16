from django.urls import path
from .site_config_api_view import HeroSectionActivateView, HeroSectionDetailUpdateDestroyView, HeroSectionListCreateView, HeroSectionPublicView

urlpatterns = [
    path('hero/', HeroSectionPublicView.as_view(), name='hero-public'),
    
    path('admin/hero/', HeroSectionListCreateView.as_view(), name='hero-list-create'),
    path('admin/hero/<int:pk>/', HeroSectionDetailUpdateDestroyView.as_view(), name='hero-detail'),
    path('admin/hero/<int:pk>/activate/', HeroSectionActivateView.as_view(), name='hero-activate'),
]