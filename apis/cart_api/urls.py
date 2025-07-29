from django.urls import path
from .cart_api_view import CartItemCreateView, CartItemDestroyView, CartDetailView, CartItemUpdateView

urlpatterns = [
    path('my-cart/', CartDetailView.as_view(), name='my-cart-detail'),

    path('items/add/', CartItemCreateView.as_view(), name='cart-item-add'),

    path('item/remove/<int:pk>/', CartItemDestroyView.as_view(), name='cart-item-remove'),

    path('items/update/<int:pk>/', CartItemUpdateView.as_view(), name='cart-item-update'),
]