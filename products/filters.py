from django_filters import rest_framework as filters
from .models import Product, Category, Essence

class ProductFilterSet(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')

    category = filters.ModelMultipleChoiceFilter(
        field_name='category__slug',
        to_field_name='slug',
        queryset=Category.objects.filter(is_active=True)
    )
    essence = filters.ModelMultipleChoiceFilter(
        field_name='essence__slug', 
        to_field_name='slug',       
        queryset=Essence.objects.filter(is_active=True)
    )

    class Meta:
        model = Product
        fields = ['category', 'essence', 'min_price', 'max_price']

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        return qs.filter(is_active=True)