from django.urls import path, include
from rest_framework import routers
from rest_framework.routers import DefaultRouter
from .products_api_view import ProductListCreateView, ProductRetrieveUpdateDestroyView, ProductFilter

router = DefaultRouter()

router.register(r'filtered_products', ProductFilter, basename='filtered-product')


urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='products-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail-view'),
    path('', include(router.urls))
]