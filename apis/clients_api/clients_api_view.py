from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import timedelta
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import CustomUser, Address
from accounts.serializers import AddressSerializer, ClientSerializer, UserClientRegisterSerializer
from django.utils.decorators import method_decorator
from apis.decorators import ratelimit_login, ratelimit_register, ratelimit_password_reset, ratelimit_profile_update, ratelimit_address
from apis.utils.security_logger import log_security_event



#APIS Views de clientes e usuários

@method_decorator(ratelimit_register, name='dispatch')
class UserRegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserClientRegisterSerializer


@method_decorator(ratelimit_login, name='dispatch')
class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                email = request.data.get('email', 'Unknown')
                log_security_event(
                    event_type='LOGIN_SUCCESS',
                    request=request,
                    user=request.user if hasattr(request, 'user') else None,
                    details=f'Login realizado com sucesso {email}',
                    level='info'
                )
            
                data = response.data
                access_token = data.get("access")
                refresh_token = data.get("refresh")
                if access_token:
                    response.set_cookie(
                        key="access_token",
                        value=access_token,
                        httponly=True,
                        secure=True,#mudar para true em prdoução
                        samesite="Lax",
                        max_age=int(timedelta(minutes=15).total_seconds()),
                        path="/",
                    )
                    del data["access"]

                if refresh_token:
                        response.set_cookie(
                            key="refresh_token",
                            value=refresh_token,
                            httponly=True,
                            secure=True, #mudar para true em prdoução
                            samesite="Lax",
                            max_age=int(timedelta(days=7).total_seconds()),  
                            path="/",  
                        )
                        del data["refresh"]
                    
                response.data = data
                
            return response
            
        except Exception as e:
            log_security_event(
                event_type='LOGIN_FAILED',
                request=request,
                details=f'Credenciais inválidas',
                level='warning'
            )
            raise


@method_decorator(ratelimit_login, name='dispatch')
class CookieTokenRefreshView(TokenRefreshView):
    """
    Substitui a TokenRefreshView padrão para ler o refresh_token 
    de um cookie HttpOnly e setar o novo access_token em um cookie.
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            log_security_event(
                event_type='TOKEN_REFRESH_FAILED',
                request=request,
                details='Refresh token não encontrado nos cookies',
                level='warning'
            )
            return Response(
                {"error": "Refresh token não encontrado."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        mutable_data = request.data.copy()
        mutable_data['refresh'] = refresh_token
        
        serializer = self.get_serializer(data=mutable_data)

        try:
            serializer.is_valid(raise_exception=True)
        except InvalidToken as e:
            log_security_event('REFRESH_INVALID', request, details=str(e))
            return Response({'error': 'Refresh token inválido ou expirado.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        data = serializer.validated_data
        access_token = data.get('access')
        
        response = Response(status=status.HTTP_200_OK)
        
        access_expires_seconds = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
        access_expires = timezone.now() + timedelta(seconds=access_expires_seconds)
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,  #True em produção
            samesite="Lax",
            expires=access_expires
        )
        
        if 'refresh' in data:
            refresh_token_new = data.get('refresh')
            refresh_expires_seconds = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
            refresh_expires = timezone.now() + timedelta(seconds=refresh_expires_seconds)
            
            response.set_cookie(
                key="refresh_token",
                value=refresh_token_new,
                httponly=True,
                secure=True,  # True em produção
                samesite="Lax",
                expires=refresh_expires
            )
        
        response.data = {'message': 'Token atualizado com sucesso.'} 
        return response

@method_decorator(ratelimit_profile_update, name='dispatch')
class ClientProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@method_decorator(ratelimit_address, name='dispatch')
class AddressCreateView(generics.CreateAPIView):
    """
    View para um utilizador autenticado criar um novo endereço.
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StatesListView(APIView):
    """
    View que retorna a lista de estados brasileiros para popular formulários.
    """
    def get(self, request, format=None):
        states = Address.ESTADOS_BRASIL
        formatted_states = [{'value': abbr, 'label': name} for abbr, name in states]
        return Response(formatted_states)
    

class AddressListView(generics.ListAPIView):
    """
    View para um usuário autenticado ver a sua lista de endereços salvos.
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


@method_decorator(ratelimit_address, name='dispatch')
class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para ler, atualizar ou apagar um endereço específico
    do utilizador autenticado.
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class UserLogoutView(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
        response = Response({'message': 'Logout realizado.'}, status=200)
        
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        
        return response


@method_decorator(ratelimit_password_reset, name='dispatch')
class UserForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email é obrigatório.'}, status=400)
        else:
            if CustomUser.objects.filter(email=email).exists():
                user = CustomUser.objects.filter(email=email).first() 

                if user:
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    reset_url = f'https://### URL_DO_SITE ###/alterar-senha/{uid}/{token}'

                    send_mail(
                        'Redefinição de Senha',
                        f'Clique no link para redefinir a sua senha: {reset_url}',
                        'bruno.rsilva2004@gmail.com',
                        [email],
                        fail_silently=False
                    )


                return Response({'message': 'Email de redefinição de senha enviado.'}, status=200)
            else:
                return Response({'error': 'Email não encontrado.'}, status=404)



# API que valida o UID e Token para redefinir a senha
@method_decorator(ratelimit_password_reset, name='dispatch')
class UserPasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            new_password = request.data.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Senha redefinida com sucesso.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'A nova senha é obrigatória.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Token inválido ou expirado.'}, status=status.HTTP_400_BAD_REQUEST)