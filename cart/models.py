from django.db import models
from django.conf import settings
from products.models import Product, Essence, ProductCustomization

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Usuário')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    def get_total(self):
        return sum(item.total_price for item in self.items.all())
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE, verbose_name='ID do Carrinho')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Produto')
    essence = models.ForeignKey(Essence, on_delete=models.SET_NULL, null=True, verbose_name='Essência')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantidade')

    @property
    def unit_price(self):
        """Calcula o preço unitário base + personalizações"""
        base_price = self.product.price
        customization_cost = 0

        for customization in self.customizations.all():
            customization_cost += customization.get_cost(self.quantity)

        return base_price + customization_cost

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    class Meta:
        ordering = ['-cart']
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'


class CartItemCustomization(models.Model):
    """
    Guarda a resposta específica do cliente para uma opção de personalização.
    """
    cart_item = models.ForeignKey(
        CartItem,
        related_name='customizations',
        on_delete=models.CASCADE
    )
    option = models.ForeignKey(
        ProductCustomization,
        on_delete=models.PROTECT,
        verbose_name='Opção Escolhida'
    )
    value = models.CharField(max_length=255,
                             verbose_name='Valor/Texto')

    def get_cost(self, item_quantity):
        """
        Calcula o custo dessa personalização baseado na regra de quantidade.
        """
        if self.option.free_above_quantity and item_quantity >= self.option.free_above_quantity:
            return 0

        return self.option.price_extra

    def __str__(self):
        return f"{self.option.name}: {self.value}"

