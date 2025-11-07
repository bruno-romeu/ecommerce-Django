from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código do Cupom")
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Percentual de Desconto"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    valid_from = models.DateTimeField(verbose_name="Válido de")
    valid_until = models.DateTimeField(verbose_name="Válido até")
    usage_limit = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Limite de Uso",
        help_text="Deixe em branco para uso ilimitado"
    )
    times_used = models.PositiveIntegerField(default=0, verbose_name="Vezes Usado")
    minimum_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor Mínimo de Compra"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Cupom de Desconto"
        verbose_name_plural = "Cupons de Desconto"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.discount_percentage}%"
    
    def is_valid(self, order_total=0):
        now = timezone.now()
        
        if not self.is_active:
            return False, "Cupom inativo"
        
        if now < self.valid_from:
            return False, "Cupom ainda não está válido"
        
        if now > self.valid_until:
            return False, "Cupom expirado"
        
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, "Cupom atingiu o limite de uso"
        
        if order_total < self.minimum_purchase:
            return False, f"Valor mínimo de compra: R$ {self.minimum_purchase}"
        
        return True, "Cupom válido"
    
    def calculate_discount(self, order_total):
        discount = (order_total * self.discount_percentage) / 100
        return float(discount)


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

