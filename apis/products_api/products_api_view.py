from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from products.models import Product, Size, Essence, Category
from products.serializers import (CategorySerializer, EssenceSerializer,
                                  ProductSerializer, SizeSerializer, ProductCustomizationSerializer)
from products.filters import ProductFilterSet


    
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True) 
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_class = ProductFilterSet 
    search_fields = ['name', 'short_description', 'full_description', 'category__name', 'essence__name', 'size__name']
    ordering_fields = ['price', 'name', 'created_at'] 

    ordering = ['-created_at']

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        product_serializer = self.get_serializer(instance)
        product_data = product_serializer.data

        all_sizes = Size.objects.all()
        available_essences = instance.category.essences.filter(is_active=True)
        customizations = instance.category.customization_options.all()

        size_serializer = SizeSerializer(all_sizes, many=True)
        essence_serializer = EssenceSerializer(available_essences, many=True, context={'request': request})

        response_data = {
            'product': product_data,
            'available_options': {
                'sizes': size_serializer.data,
                'essences': essence_serializer.data,
                'customizations': ProductCustomizationSerializer(customizations, many=True).data
            }
        }

        return Response(response_data)

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class BestSellerListView(generics.ListAPIView):
    """
    Retorna uma lista de produtos marcados como 'is_bestseller=True'.
    """
    queryset = Product.objects.filter(is_bestseller=True, is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class EssenceListView(generics.ListAPIView):
    queryset = Essence.objects.filter(is_active=True)
    serializer_class = EssenceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]