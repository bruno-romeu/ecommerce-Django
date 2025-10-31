from django.urls import path, include
from apis.clients_api.clients_api_view import UserDetailView

urlpatterns = [
    path('client/', include('apis.clients_api.urls')),
    path('product/', include('apis.products_api.urls')),
    path('cart/', include('apis.cart_api.urls')),
    path('order/', include('apis.orders_api.urls')),
    path('checkout/', include('apis.checkout_api.urls')),
    path('site-config/', include('apis.site_config_api.urls')),
    path('auth/users/me/', UserDetailView.as_view(), name='user_detail'),


]