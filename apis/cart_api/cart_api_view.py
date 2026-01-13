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
import re 
logger = logging.getLogger(__name__)


def validar_cep(cep):
    """
    Valida formato de CEP brasileiro (XXXXX-XXX ou XXXXXXXX)
    Retorna: (bool, str) - (é_válido, mensagem_erro)
    """
    if not cep:
        return False, "CEP é obrigatório"
    
    cep_limpo = re.sub(r'[^0-9]', '', cep)
    
    if len(cep_limpo) != 8:
        return False, "CEP deve conter exatamente 8 dígitos"
    
    if cep_limpo in ['00000000', '11111111', '22222222', '33333333', 
                     '44444444', '55555555', '66666666', '77777777', 
                     '88888888', '99999999']:
        return False, "CEP inválido"
    
    return True, cep_limpo


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
    View que retorna o valor da cotação do frete, com base nos CEPs 
    de origem e destino, e os produtos que estão no carrinho do cliente.
    '''
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        cep_origem = '93800192'
        cep_destino = request.data.get('cep', '').strip()

        cep_valido, resultado = validar_cep(cep_destino)
        
        if not cep_valido:
            logger.warning(
                f"[FRETE] CEP inválido fornecido por usuário {request.user.id}: '{cep_destino}'"
            )
            return Response(
                {
                    "error": resultado,
                    "field": "cep"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cep_destino = resultado

        cart_items = CartItem.objects.filter(
            cart__user=request.user
        ).select_related('product', 'product__size')

        if not cart_items:
            return Response(
                {"error": "Seu carrinho está vazio."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        products_data = []
        for item in cart_items:
            if not item.product or not item.product.size:
                logger.error(
                    f"[FRETE] Produto {item.product.id if item.product else 'N/A'} "
                    f"sem tamanho configurado"
                )
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
                logger.error(f"[FRETE] Erro ao processar produto {item.product.id}: {str(e)}")
                return Response(
                    {"error": "Erro ao processar item. Tente novamente."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        if not products_data:
            return Response(
                {"error": "Nenhum produto válido encontrado no carrinho."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            shipping_options = calcular_frete_melhor_envio(
                cep_origem=cep_origem, 
                cep_destino=cep_destino,
                product_list=products_data
            )

            services_data = []
            for option in shipping_options:
                if 'price' in option and 'delivery_time' in option:
                    services_data.append({
                        'id':option['id'],
                        'servico': option['name'],
                        'preco': option['price'],
                        'prazo': option['delivery_time'],
                        'transportadora': option.get('company', {}.get('name'))
                    })

            if not services_data:
                logger.warning(
                    f"[FRETE] Nenhum serviço disponível para CEP {cep_destino}"
                )
                return Response(
                    {"error": "Nenhum serviço de frete disponível para este CEP."},
                    status=status.HTTP_404_NOT_FOUND
                )

            logger.info(
                f"[FRETE] {len(services_data)} opções calculadas para "
                f"usuário {request.user.id}, CEP {cep_destino}"
            )

            return Response(services_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[FRETE] Erro ao calcular frete: {str(e)}")
            return Response(
                {"error": f"Erro ao calcular frete: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            


    
