from django.urls import path, include

urlpatterns = [
    path('client/', include('apis.clients_api.urls')),
    path('product/', include('apis.products_api.urls')),
    path('cart/', include('apis.cart_api.urls')),
    path('order/', include('apis.orders_api.urls')),
    path('checkout/', include('apis.checkout_api.urls')),
    path('site-config/', include('apis.site_config_api.urls')),

]