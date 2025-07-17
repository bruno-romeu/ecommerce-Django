from django.urls import path, include

urlpatterns = [
    path('client/', include('apis.clients_api.urls')),
    path('product/', include('apis.products_api.urls')),

]