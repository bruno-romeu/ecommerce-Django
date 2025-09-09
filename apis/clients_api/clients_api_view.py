from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth import logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from accounts.models import CustomUser
from accounts.serializers import AddressSerializer, ClientSerializer, UserClientRegisterSerializer


#APIS Views de clientes e usuários

class UserRegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserClientRegisterSerializer

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        return Response({'token': token.key, 'user_id': token.user_id})


class ClientProfileView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    lookup_field = 'id'
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return CustomUser.objects.get(user=self.request.user)



class UserLogoutView(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({'message': 'Logout realizado.'}, status=200)
    
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