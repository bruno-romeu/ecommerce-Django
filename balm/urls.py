from django.contrib import admin
from django.urls import path, include
from apis.clients_api.clients_api_view import UserDetailView

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apis.urls')),
    path('auth/users/me/', UserDetailView.as_view(), name='user_detail')
,
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
