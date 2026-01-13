from django.db import models
from django.conf import settings
from products.models import Product

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Usuário')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    def get_total(self):
        return sum(item.product.price * item.quantity for item in self.items.all())
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE, verbose_name='ID do Carrinho')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Produto')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantidade')

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    class Meta:
        ordering = ['-cart']
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'

