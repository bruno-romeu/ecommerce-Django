from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Client

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class UserClientRegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=False)
    birthday = serializers.DateField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone', 'birthday']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        phone = validated_data.pop('phone', None)
        birthday = validated_data.pop('birthday', None)

        email_exists = User.objects.filter(email=validated_data['email']).exists()
        
        if email_exists:
            raise serializers.ValidationError("O email informado já está cadastrado.")
        else:
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data.get('email'),
                password=validated_data['password']
            )
            Client.objects.create(user=user, phone=phone, birthday=birthday)
            return user