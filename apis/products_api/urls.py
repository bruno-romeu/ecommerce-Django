from django.urls import path, include
from rest_framework import routers
from rest_framework.routers import DefaultRouter
from .products_api_view import ProductViewSet, CategoryListView, BestSellerListView, EssenceListView

router = DefaultRouter()

router.register(r'products', ProductViewSet, basename='product')


urlpatterns = [
    path('', include(router.urls)),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('bestsellers/', BestSellerListView.as_view(), name='bestseller-list'),
    path('essences/', EssenceListView.as_view(), name='essence-list'),
]