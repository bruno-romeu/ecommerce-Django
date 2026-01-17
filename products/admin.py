from django.contrib import admin
from .models import Category, Essence, Product, Size, ProductCustomization

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active',)
    search_fields = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Essence)
class EssenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'sensory_profile', 'notes', 'ambient', 'order',
                    'is_active',)
    search_fields = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_description' , 'price' , 'stock_quantity' , 'category', 'size' , 'is_bestseller' , 'is_active',)
    search_fields = ('name', 'slug', 'category', 'size',)
    list_filter = ('category', 'size', 'is_active',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)

    autocomplete_fields = ('category', 'size',)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'weight', 'unit', 'height', 'width',
                    'length',)
    search_fields = ('name',)

@admin.register(ProductCustomization)
class ProductCustomizationAdmin(admin.ModelAdmin):
    list_display = ('category', 'name', 'instruction', 'input_type',
                    'available_options', 'price_extra',
                    'free_above_quantity',)
    search_fields = ('category', 'name',)




