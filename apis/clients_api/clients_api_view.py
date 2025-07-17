from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from clients.models import Client
from clients.serializers import ClientSerializer, UserClientRegisterSerializer


#APIS Views de clientes e usuários

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserClientRegisterSerializer

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        return Response({'token': token.key, 'user_id': token.user_id})

class ClientProfileView(generics.RetrieveAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Client.objects.get(user=self.request.user)

class UserLogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'message': 'Logout realizado.'}, status=200)
    
class UserForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email é obrigatório.'}, status=400)
        else:
            if User.objects.filter(email=email).exists():
                user = User.objects.filter(email=email).first() 

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



#fazer API que valida o UID e Token para redefinir a senha