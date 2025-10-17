from django_filters import rest_framework as filters
from .models import Product

class ProductFilterSet(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')

    category = filters.CharFilter(field_name='category__slug', lookup_expr='in')
    essence = filters.CharFilter(field_name='essence__slug', lookup_expr='in')

    class Meta:
        model = Product
        fields = ['category', 'essence', 'min_price', 'max_price']