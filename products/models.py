from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    slug = models.SlugField(unique=True, blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True,
                              verbose_name='Imagem',
                              validators=[FileExtensionValidator(
                                  allowed_extensions=['jpg', 'jpeg', 'png',])],)
    is_active = models.BooleanField(default=True, verbose_name='Ativo')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
    
class Essence(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    sensory_profile = models.CharField(max_length=100, verbose_name='Perfil Sensorial', default=Null)
    notes = models.CharField(max_length=100, verbose_name='Notas Sensoriais',
                             default=Null)
    ambient = models.CharField(max_length=100, verbose_name='Ambiente',
                               default=Null)
    categories = models.ManyToManyField(Category, related_name='essences',
                               verbose_name='Categorias')
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    image = models.ImageField(upload_to="essences/", blank=True, null=True,
                              verbose_name="Imagem da Essência",
                              validators=[FileExtensionValidator(
                                  allowed_extensions=['jpg', 'jpeg', 'png',])],)
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem de Exibição")
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Essência"
        verbose_name_plural = "Essências"


    def __str__(self):
        return self.name
    
class Size(models.Model):
    UNIDADES_DE_MEDIDA = [
        ("g", "gramas"),
        ("ml", "mililitros")
    ]
    name = models.CharField(max_length=25, blank=True, null=True, verbose_name='Nome')
    weight = models.FloatField( blank=True, null=True, verbose_name='Peso')
    unit = models.CharField(max_length=2, choices=UNIDADES_DE_MEDIDA,
                            verbose_name='Unidade de Medida')
    height = models.FloatField(default=5.0, verbose_name='Altura (cm)')
    width = models.FloatField(default=3.0, verbose_name='Largura (cm)')
    length = models.FloatField(default=3.0, verbose_name='Comprimento (cm)')
    diameter = models.FloatField(blank=True, null=True, verbose_name='Diâmetro (cm)')
    circumference = models.FloatField(blank=True, null=True, verbose_name='Circunferência (cm)')

    def __str__(self):
        return f'{self.name} - {self.weight} {self.unit}'

    class Meta:
        verbose_name = 'Tamanho'
        verbose_name_plural = 'Tamanhos'
    
class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    short_description = models.TextField(blank=True, verbose_name='Descrição Curta')
    full_description = models.TextField(blank=True, verbose_name='Descrição Completa')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Preço')
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name='Quantidade')
    stock = models.BooleanField(verbose_name='Em Estoque?', default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='Categoria')
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name='Tamanho')
    is_bestseller = models.BooleanField(default=False, verbose_name="Best-seller")
    image = models.ImageField(upload_to='products/', blank=True, null=True,
                              verbose_name='Imagem',
                              validators=[FileExtensionValidator(
                                  allowed_extensions=['jpg', 'jpeg', 'png',])])
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação", null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            # Verificar se o slug já existe e adicionar número se necessário
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name', 'price', 'stock_quantity', 'category', 'size', 'is_bestseller', 'created_at']
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"



class ProductCustomization(models.Model):
    """
    Define as opções de personalização disponíveis para um produto.
    Ex: 'Gravar Nome' (Texto)
    """
    TYPE_CHOICES = (
        ('text', 'Texto Livre (Cliente digita)'),
        ('select', 'Seleção (Cliente escolhe de uma lista)'),
        ('boolean', 'Sim/Não'),
    )

    category = models.ForeignKey(Category,
                                 related_name='customization_options',
                          on_delete=models.CASCADE, verbose_name='Categoria',
    default=5
    )
    name = models.CharField(max_length=100, verbose_name='Nome da Opção')
    instruction = models.CharField(max_length=255, blank=True,
                                   verbose_name='Instrução para o cliente')

    input_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text', verbose_name='Tipo de Entrada')

    available_options = models.TextField(blank=True,
                                         null=True,
                                         verbose_name='Opções disponíveis (se houver)')

    price_extra = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name='Custo Adicional (Unitário)'
    )
    free_above_quantity = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Grátis a partir de X unidades',
        help_text='Se o cliente comprar acima dessa quantidade, essa personalização sai de graça.'
    )

    def __str__(self):
        return f"{self.name} - {self.category.name}"

