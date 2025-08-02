from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Client

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class UserClientRegisterSerializer(serializers.ModelSerializer):
    birthday = serializers.DateField(write_only=True, required=False)
    phone = serializers.CharField(write_only=True, required=False)
    cpf = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=255, required=True)

    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [ 'first_name', 'last_name', 'email', 'password', 'confirm_password', 'phone', 'cpf', 'birthday']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "As senhas devem ser iguais."})
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'Este email já está cadastrado.'})
        return data 

    def create(self, validated_data):
        phone = validated_data.pop('phone', None)
        birthday = validated_data.pop('birthday', None)
        cpf = validated_data.pop('cpf')
        validated_data.pop('confirm_password')

        first_name = validated_data['first_name'].strip().capitalize()
        last_name = validated_data['last_name'].strip().capitalize()
        full_name = first_name + ' ' + last_name
        username = full_name

        validated_data['username'] = username
        

        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        Client.objects.create(user=user, cpf=cpf, phone=phone, birthday=birthday)

        return user