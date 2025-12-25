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
from accounts.utils import send_verification_email, is_verification_token_valid
from django.utils.decorators import method_decorator
from apis.decorators import ratelimit_login, ratelimit_register, ratelimit_password_reset, ratelimit_profile_update, ratelimit_address
from apis.utils.security_logger import log_security_event




#APIS Views de clientes e usuários

@method_decorator(ratelimit_register, name='dispatch')
class UserRegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserClientRegisterSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == 201:
            user_email = request.data.get('email')
            try:
                user = CustomUser.objects.get(email=user_email)
                send_verification_email(user)
                
                log_security_event(
                    event_type='USER_REGISTERED',
                    request=request,
                    user=user,
                    details=f'Novo usuário registrado: {user_email}. Email de verificação enviado.',
                    level='info'
                )
            except CustomUser.DoesNotExist:
                pass
        
        return response


@method_decorator(ratelimit_login, name='dispatch')
class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        try:
            response = super().post(request, *args, **kwargs)
        except Exception as e:
            log_security_event(
                event_type='LOGIN_FAILED',
                request=request,
                details=f'Credenciais inválidas para email: {email}',
                level='warning'
            )
            raise

        if response.status_code == 200:
            try:
                user = CustomUser.objects.get(email=email)

                if not user.email_verified:
                    log_security_event(
                        event_type='LOGIN_BLOCKED_UNVERIFIED',
                        request=request,
                        user=user,
                        details=f'Tentativa de login com email não verificado: {email}',
                        level='warning'
                    )
                    return Response({
                        'error': 'Email não verificado. Por favor, verifique seu email antes de fazer login.',
                        'email_verified': False
                    }, status=status.HTTP_403_FORBIDDEN)

                log_security_event(
                    event_type='LOGIN_SUCCESS',
                    request=request,
                    user=user,
                    details=f'Login realizado com sucesso para {email}',
                    level='info'
                )

                data = response.data
                access_token = data.get("access")
                refresh_token = data.get("refresh")
                access_expires = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
                refresh_expires = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']

                if access_token:
                    response.set_cookie(
                        key="access_token",
                        value=access_token,
                        httponly=True,
                        secure=True,  # True em produção
                        samesite="None",
                        max_age=int(access_expires.total_seconds()),
                        path="/",
                    )
                    del data["access"]

                if refresh_token:
                    response.set_cookie(
                        key="refresh_token",
                        value=refresh_token,
                        httponly=True,
                        secure=True,  # True em produção
                        samesite="None",
                        max_age=int(refresh_expires.total_seconds()),
                        path="/",
                    )
                    del data["refresh"]

                response.data = data

            except CustomUser.DoesNotExist:
                pass

        return response


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
            samesite="None",
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
                samesite="None",
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
        
class UserDetailView(APIView):
    """
    View para retornar os dados do usuário autenticado.
    O JWTAuthCookieMiddleware cuida da autenticação lendo o cookie.
    """
    permission_classes = [permissions.IsAuthenticated] 
    def get(self, request, *args, **kwargs):
        """
        Retorna os dados do usuário logado (request.user).
        """
        try:
            serializer = ClientSerializer(request.user) 
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            log_security_event(
                'USER_DETAIL_FAIL', 
                request, 
                user=request.user, 
                details=f"Erro ao serializar usuário: {str(e)}"
            )
            return Response(
                {'error': 'Erro ao obter dados do usuário.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

#views de verificação de email ao registrar e logar
class VerifyEmailView(APIView):
    """
    View para verificar o email do usuário através do token
    """
    permission_classes = [] 
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token de verificação é obrigatório.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email_verification_token=token)
            
            if not is_verification_token_valid(user):
                log_security_event(
                    event_type='EMAIL_VERIFICATION_EXPIRED',
                    request=request,
                    user=user,
                    details='Token de verificação expirado',
                    level='warning'
                )
                return Response({
                    'error': 'Token de verificação expirado. Solicite um novo email de verificação.',
                    'expired': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.email_verified = True
            user.email_verification_token = None  # Limpa o token usado
            user.save(update_fields=['email_verified', 'email_verification_token'])
            
            log_security_event(
                event_type='EMAIL_VERIFIED',
                request=request,
                user=user,
                details=f'Email verificado com sucesso: {user.email}',
                level='info'
            )
            
            return Response({
                'message': 'Email verificado com sucesso! Você já pode fazer login.',
                'email_verified': True
            }, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            log_security_event(
                event_type='EMAIL_VERIFICATION_INVALID_TOKEN',
                request=request,
                details='Token de verificação inválido',
                level='warning'
            )
            return Response({
                'error': 'Token de verificação inválido.'
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ratelimit_register, name='dispatch')
class ResendVerificationEmailView(APIView):
    """
    View para reenviar email de verificação
    """
    permission_classes = []  
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email é obrigatório.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
            
            # Verifica se o email já está verificado
            if user.email_verified:
                return Response({
                    'message': 'Este email já está verificado. Você pode fazer login.'
                }, status=status.HTTP_200_OK)
            
            # Verifica se já enviou recentemente (evita spam)
            if user.email_verification_sent_at:
                time_since_last_email = timezone.now() - user.email_verification_sent_at
                if time_since_last_email < timedelta(minutes=5):
                    return Response({
                        'error': 'Um email de verificação já foi enviado recentemente. Aguarde 5 minutos antes de solicitar novamente.'
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            if send_verification_email(user):
                log_security_event(
                    event_type='VERIFICATION_EMAIL_RESENT',
                    request=request,
                    user=user,
                    details=f'Email de verificação reenviado para: {user.email}',
                    level='info'
                )
                return Response({
                    'message': 'Email de verificação enviado com sucesso. Verifique sua caixa de entrada.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Erro ao enviar email de verificação. Tente novamente mais tarde.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except CustomUser.DoesNotExist:
            return Response({
                'message': 'Se este email estiver cadastrado, você receberá um email de verificação.'
            }, status=status.HTTP_200_OK)