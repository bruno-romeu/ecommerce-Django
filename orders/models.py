from django.db import models
from products.models import Product
from accounts.models import CustomUser, Address


class Order(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('processing', 'Em Separação'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregue'),
        ('canceled', 'Cancelado'),
    ]

    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders', verbose_name='Cliente')
    address = models.ForeignKey(Address, on_delete=models.PROTECT, verbose_name='Endereço')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, verbose_name='Custo de Entrega')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Total')

    def __str__(self):
        return f'Pedido #{self.id}'
    
    def get_total_with_shipping(self):
        return (self.total + self.shipping_cost)

    @property
    def payment_status(self):
        return self.payment.status if hasattr(self, 'payment') and self.payment else 'Sem pagamento'

    @property
    def shipping_status(self):
        return self.shipping.status if hasattr(self, 'shipping') and self.shipping else 'Sem envio'
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Pedido')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Produto')
    quantity = models.PositiveIntegerField(verbose_name='Quantidade')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Preço')
    customization_details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Detalhes da Personalização'
    )

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

