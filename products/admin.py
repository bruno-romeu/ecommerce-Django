from django.contrib import admin
from .models import Category, Essence, Product, Size

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'slug',)
    search_fields = ('name',)

@admin.register(Essence)
class EssenceAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'description' , 'price' , 'stock' , 'category' , 'essence' , 'size' , 'image' , 'is_active',)
    search_fields = ('name', 'category', 'essence', 'size',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'weight', 'height', 'width', 'length', 'diameter', 'circumference',)


