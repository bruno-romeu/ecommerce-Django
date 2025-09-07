from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Essence(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
class Size(models.Model):
    name = models.CharField(max_length=25, blank=True, null=True)
    weight = models.FloatField("Weight (kg)", blank=True, null=True)
    height = models.FloatField("Height (cm)", default=5.0)
    width = models.FloatField("Width (cm)", default=3.0)
    length = models.FloatField("Length (cm)", default=3.0)
    diameter = models.FloatField("Diameter (cm)", blank=True, null=True)
    circumference = models.FloatField("Circumference (cm)", blank=True, null=True)

    def __str__(self):
        return f'{self.name} - {self.weight}kg'

    class Meta:
        verbose_name = 'Size'
        verbose_name_plural = 'Sizes'
    
class Product(models.Model):
    name = models.CharField(max_length=100)
    short_description = models.TextField(blank=True)
    full_description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    stock = models.BooleanField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    essence = models.ForeignKey(Essence, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    is_bestseller = models.BooleanField(default=False, verbose_name="É um mais vendido?")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

