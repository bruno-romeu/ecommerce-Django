from django.db import models

class HeroSection(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título Principal")
    subtitle = models.TextField(blank=True, verbose_name="Subtítulo (Opcional)")
    button_text = models.CharField(max_length=50, verbose_name="Texto do Botão")
    button_link = models.CharField(max_length=255, verbose_name="Link do Botão (ex: /produtos)")
    background_image = models.ImageField(upload_to='hero/', verbose_name="Imagem de Fundo")
    is_active = models.BooleanField(default=False, verbose_name="Ativo")

    class Meta:
        verbose_name = "Banner inicial"
        verbose_name_plural = "Banners iniciais"
        ordering = ['-is_active']

    def __str__(self):
        return self.title   