from django.db import models
from clients.models import Client

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
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='addresses')
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2, choices=ESTADOS_BRASIL)
    zipcode = models.CharField(max_length=10)
    complement = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.street}, {self.number} - {self.city}/{self.state} - CEP: {self.zipcode}'


class Shipping(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregue'),
        ('returned', 'Devolvido'),
    ]

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='shipping')
    tracking_code = models.CharField(max_length=50, blank=True, null=True)
    carrier = models.CharField(max_length=50, blank=True, null=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    estimated_delivery = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    updated_at = models.DateTimeField(auto_now=True)


class Payment(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('failed', 'Falhou'),
        ('refunded', 'Reembolsado'),
    ]


    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)

