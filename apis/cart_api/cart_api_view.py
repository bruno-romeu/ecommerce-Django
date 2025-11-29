from rest_framework import generics, status, request, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from cart.models import Cart, CartItem
from orders.models import Order
from cart.serializers import CartSerializer, CartItemSerializer
from cart.utils import calcular_frete_melhor_envio
from django.utils.decorators import method_decorator
from apis.decorators import ratelimit_cart
import logging                          
logger = logging.getLogger(__name__)

@method_decorator(ratelimit_cart, name='dispatch')
class CartItemCreateView(generics.CreateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        serializer = self.get_serializer(data=request.data) 
        serializer.is_valid(raise_exception=True)
        
        product = serializer.validated_data.get('product')
        quantity = serializer.validated_data.get('quantity', 1)

        existing_item = CartItem.objects.filter(cart=cart, product=product).first()

        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
            
            response_serializer = self.get_serializer(existing_item)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        else:
            serializer.save(cart=cart)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



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

class CalculateShippingView(views.APIView):
    '''
    View que retorna o valor da cotação do frete, com base nos fretes de origem e destino, e os produtos que estão no carrinho do cliente.
    '''
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        cep_origem = '93800192'
        cep_destino = request.data.get('cep', '').strip()

        if not cep_destino:
            return Response(
                {"error": "O CEP destino é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )

        products_data = []
        services_data = []

        cart_items = CartItem.objects.filter(
            cart__user=request.user
        ).select_related('product', 'product__size')

        if not cart_items:
            return Response(
                {"error": "Seu carrinho está vazio."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        for item in cart_items:
            if not item.product or not item.product.size:
                continue
            product_size = item.product.size

            try:
                products_data.append({
                    'weight': product_size.weight,
                    'width': product_size.width,
                    'height': product_size.height,
                    'length': product_size.length,
                    'quantity': item.quantity
                })
            except Exception as e:
                logger.error(f"Erro ao processar produto {item.product.id}: {str(e)}")
                return Response(
                    {"error": "Erro ao processar item. Tente novamente."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        if cep_origem and cep_destino and products_data:
        
            try:
                shipping_options = calcular_frete_melhor_envio(
                    cep_origem=cep_origem, 
                    cep_destino=cep_destino,
                    product_list=products_data
                )

                for option in shipping_options:
                    if 'price' in option and 'delivery_time' in option:
                        services_data.append({
                            'servico':option['name'],
                            'preco':option['price'],
                            'prazo':option['delivery_time']
                        })


            except Exception as e:
                return Response(
                    {"error": f"Erro ao calcular frete com a API: {e}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(services_data, status=status.HTTP_200_OK)
            
            


    
