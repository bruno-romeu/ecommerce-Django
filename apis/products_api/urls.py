from django.urls import path
from .products_api_view import ProductListCreateView, ProductRetrieveUpdateDestroyView

urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='products-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail-view'),
]