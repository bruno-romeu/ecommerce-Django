from django.urls import path
from apis.clients_api.clients_api_view import UserRegisterView, ClientProfileView, UserForgotPasswordView, UserLogoutView, UserPasswordResetConfirmView, AddressCreateView, StatesListView, AddressListView, AddressDetailView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('profile/', ClientProfileView.as_view(), name='client-profile'),
    path('address/create/', AddressCreateView.as_view(), name='address-create'),
    path('utils/states/', StatesListView.as_view(), name='states-list'),
    path('addresses/', AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('forgot-password/', UserForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<str:uidb64>/<str:token>/', UserPasswordResetConfirmView.as_view(), name='reset-password-confirm'),


]