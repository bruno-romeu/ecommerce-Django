from django.urls import path
from .orders_api_view import OrderCreateView, OrderListView, OrderDetailView, OrderStatusUpdateView, OrderCancelView

urlpatterns = [
    path('order-create/', OrderCreateView.as_view(), name='order-create'),

    path('order-list/', OrderListView.as_view(), name='order-list'),

    path('order-detail/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),

    path('order-cancel/<int:pk>/', OrderCancelView.as_view(), name='order-cancel'),

    path('order-status-update/<int:pk>/', OrderStatusUpdateView.as_view(), name='order-status-update')

]