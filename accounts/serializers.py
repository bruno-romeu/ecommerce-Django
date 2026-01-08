from rest_framework import serializers
from .models import CustomUser, Address
import re 


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ('user',)
    
    def validate_zipcode(self, value):
        """
        Valida o CEP (zipcode) do endereço
        """
        if not value:
            raise serializers.ValidationError("CEP é obrigatório.")
        
        cep_limpo = re.sub(r'[^0-9]', '', value)
        
        if len(cep_limpo) != 8:
            raise serializers.ValidationError(
                "CEP deve conter exatamente 8 dígitos."
            )
        
        ceps_invalidos = [
            '00000000', '11111111', '22222222', '33333333', 
            '44444444', '55555555', '66666666', '77777777', 
            '88888888', '99999999'
        ]
        
        if cep_limpo in ceps_invalidos:
            raise serializers.ValidationError("CEP inválido.")
        
        return f"{cep_limpo[:5]}-{cep_limpo[5:]}"
    
    def validate_state(self, value):
        """
        Valida se o estado é uma sigla válida
        """
        estados_validos = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
            'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
            'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]
        
        value_upper = value.upper()
        
        if value_upper not in estados_validos:
            raise serializers.ValidationError(
                f"Estado inválido. Use uma sigla válida (ex: SP, RJ, RS)."
            )
        
        return value_upper
    
    def validate_street(self, value):
        """
        Valida se a rua não está vazia
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Rua é obrigatória.")
        
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Nome da rua deve ter no mínimo 3 caracteres."
            )
        
        return value.strip()
    
    def validate_number(self, value):
        """
        Valida o número do endereço
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Número é obrigatório.")
        
        return value.strip()
    
    def validate_city(self, value):
        """
        Valida a cidade
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Cidade é obrigatória.")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Nome da cidade deve ter no mínimo 2 caracteres."
            )
        
        return value.strip()
    
    def validate_neighborhood(self, value):
        """
        Valida o bairro
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Bairro é obrigatório.")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Nome do bairro deve ter no mínimo 2 caracteres."
            )
        
        return value.strip()

class ClientSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'first_name', 'last_name', 
            'cpf', 'phone_number', 'birthday', 'addresses', 
            'email_verified'
            )
        read_only_fields = ('email_verified',)

class UserClientRegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = CustomUser
        fields = [ 'first_name', 'last_name', 'email', 'password', 'password2']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data['password'] != data['password2']:   
            raise serializers.ValidationError({"password": "As senhas devem ser iguais."})
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'Este email já está cadastrado.'})
        return data 

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user