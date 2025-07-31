from django.urls import path
from apis.clients_api.clients_api_view import UserRegisterView, CustomAuthToken, ClientProfileView, UserForgotPasswordView, UserLogoutView, UserPasswordResetConfirmView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('login/', CustomAuthToken.as_view(), name='user-login'),
    path('profile/', ClientProfileView.as_view(), name='client-profile'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('forgot-password/', UserForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<str:uidb64>/<str:token>/', UserPasswordResetConfirmView.as_view(), name='reset-password-confirm'),

]