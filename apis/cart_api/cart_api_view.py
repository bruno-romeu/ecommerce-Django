from rest_framework import generics, status, request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from products.models import Product, Size
from cart.models import Cart, CartItem
from cart.serializers import CartSerializer, CartItemSerializer
from cart.utils import calcular_frete_melhor_envio

class CartItemCreateView(generics.CreateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # encontrar ou criar um carrinho para o usuário
        cart, created = Cart.objects.get_or_create(user=self.request.user)

        product = serializer.validated_data.get('product')
        quantity = serializer.validated_data.get('quantity', 1)

        # verifica se o item já existe no carrinho 
        existing_item = CartItem.objects.filter(cart=cart, product=product).first()

        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            return Response(CartItemSerializer(existing_item).data, status=status.HTTP_200_OK)
        else:
            serializer.save(cart=cart)


class CartItemDestroyView(generics.DestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # garante que o usuário só pode deletar itens do seu próprio carrinho
        return(CartItem.objects.filter(cart__user=self.request.user))
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartDetailView(generics.RetrieveAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartItemUpdateView(generics.UpdateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)
#lógica para calcular o total do carrinho está no model Cart 

class CalculateShippingView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        cep_origem = '93800192'
        cep_destino = request.data.get('cep')

        products_data = []
        for item in CartItem.objects.filter(cart__user=request.user):
            product_size = item.size

            try:
                products_data.append({
                    'id': item.product.id,
                    'weight': product_size.weight,
                    'width': product_size.width,
                    'height': product_size.height,
                    'length': product_size.length,
                    'insurance_value': item.product.price,
                    'quantity': item.quantity
                })
            except Exception as e:
                raise Exception(f"Erro ao obter dados do produto: {e}")
            
        if cep_origem and cep_destino and products_data:

            try:
                shipping_options = calcular_frete_melhor_envio(
                    cep_origem=cep_origem, 
                    cep_destino=cep_destino,
                    products=products_data
                )

                services = []
                for option in shipping_options:
                    services.append({
                        'servico':option['name'],
                        'preco':option['price'],
                        'prazo':option['delivery_time']
                    })


            except Exception as e:
                raise Exception(f"Erro ao calcular frete: {e}")
            
        return Response(services)
            
            


    
