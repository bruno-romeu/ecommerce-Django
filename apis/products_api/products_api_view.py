from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
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
    lookup_field = 'id'

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

    


#Fazer API que busca e filtra produtos 