from django.urls import path
from apis.clients_api.clients_api_view import UserRegisterView, CustomAuthToken, ClientProfileView, UserForgotPasswordView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('login/', CustomAuthToken.as_view(), name='user-login'),
    path('profile/', ClientProfileView.as_view(), name='client-profile'),
    path('forgot_password/', UserForgotPasswordView.as_view(), name='forgot_password'),

]