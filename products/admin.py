from django.contrib import admin
from .models import Category, Essence, Product, Size

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'slug',)
    search_fields = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Essence)
class EssenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'order',)
    search_fields = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'short_description' , 'price' , 'stock' , 'category' , 'essence' , 'size' , 'image' , 'is_active',)
    search_fields = ('name', 'slug', 'category', 'essence', 'size',)
    list_filter = ('category', 'essence', 'size', 'is_active',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)

    autocomplete_fields = ('category', 'essence', 'size',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'weight', 'height', 'width', 'length', 'diameter', 'circumference',)
    search_fields = ('name',)



