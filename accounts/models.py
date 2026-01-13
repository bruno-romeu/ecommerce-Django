from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from .managers import CustomUserManager

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField('endereço de email', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)

    email_verified = models.BooleanField(default=False, verbose_name='Conta Verificada')
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Registro', null=True)

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
class Address(models.Model):

    ESTADOS_BRASIL = [
        ("AC", "Acre"),
        ("AL", "Alagoas"),
        ("AP", "Amapá"),
        ("AM", "Amazonas"),
        ("BA", "Bahia"),
        ("CE", "Ceará"),
        ("DF", "Distrito Federal"),
        ("ES", "Espírito Santo"),
        ("GO", "Goiás"),
        ("MA", "Maranhão"),
        ("MT", "Mato Grosso"),
        ("MS", "Mato Grosso do Sul"),
        ("MG", "Minas Gerais"),
        ("PA", "Pará"),
        ("PB", "Paraíba"),
        ("PR", "Paraná"),
        ("PE", "Pernambuco"),
        ("PI", "Piauí"),
        ("RJ", "Rio de Janeiro"),
        ("RN", "Rio Grande do Norte"),
        ("RS", "Rio Grande do Sul"),
        ("RO", "Rondônia"),
        ("RR", "Roraima"),
        ("SC", "Santa Catarina"),
        ("SP", "São Paulo"),
        ("SE", "Sergipe"),
        ("TO", "Tocantins"),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses', verbose_name='Usuário')
    street = models.CharField(max_length=255, verbose_name='Rua')
    number = models.CharField(max_length=10, verbose_name='Número')
    neighborhood = models.CharField(max_length=100, verbose_name='Bairro')
    city = models.CharField(max_length=100, verbose_name='Cidade')
    state = models.CharField(max_length=2, choices=ESTADOS_BRASIL, verbose_name='Estado')
    zipcode = models.CharField(max_length=10, verbose_name='CEP')
    complement = models.CharField(max_length=100, blank=True, null=True, verbose_name='Complemento')

    def __str__(self):
        return f'{self.street}, {self.number} - {self.city}/{self.state} - CEP: {self.zipcode}'
    
    class Meta:
        ordering = ['id', 'state', 'user']
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'