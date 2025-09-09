from django.db import models


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

