from rest_framework import generics, viewsets, permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from products.models import Category, Essence, Product, Size
from products.serializers import CategorySerializer, EssenceSerializer, ProductSerializer, SizeSerializer

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

    
class ProductFilter(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name', 'category', 'essence', 'size']
    search_fields = ['name', 'category__name', 'essence__name', 'size__name']