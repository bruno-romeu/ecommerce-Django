from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from products.models import Product, Size, Essence, Category
from products.serializers import CategorySerializer, EssenceSerializer, ProductSerializer, SizeSerializer
from products.filters import ProductFilterSet

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]


class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        all_sizes = Size.objects.all()
        all_essences = Essence.objects.all()

        product_data = self.get_serializer(instance).data
        sizes_data = SizeSerializer(all_sizes, many=True).data
        essences_data = EssenceSerializer(all_essences, many=True).data

        response_data = {
            "product": product_data,
            "available_options": {
                "sizes": sizes_data,
                "essences": essences_data
            }
        }

        return Response(response_data)

    def get_permissions(self):

        if self.request.method == 'GET':
            permission_classes = [IsAuthenticatedOrReadOnly]

        elif self.request.method == 'PUT':
            permission_classes = [IsAdminUser]

        elif self.request.method == 'DELETE':
            permission_classes = [IsAdminUser]

        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

    
class ProductViewSet(viewsets.ModelViewSet):
    lookup_field = 'slug'
    queryset = Product.objects.filter(is_active=True) 
    serializer_class = ProductSerializer
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_class = ProductFilterSet 
    search_fields = ['name', 'short_description', 'full_description', 'category__name', 'essence__name', 'size__name']
    ordering_fields = ['price', 'name', 'created_at'] 

    ordering = ['-created_at']

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
    queryset = Essence.objects.filter(is_active=True) # Filtra apenas as ativas
    serializer_class = EssenceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]