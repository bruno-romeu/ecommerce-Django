from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from datetime import datetime, timedelta

from orders.models import Order, OrderItem
from checkout.models import Shipping
from orders.serializers import OrderSerializer, OrderStatusSerializer, OrderSerializer
from cart.models import Cart, CartItem
from django.utils.decorators import method_decorator
from apis.decorators import ratelimit_create_order
from apis.utils.security_logger import log_security_event
import re 

def validar_endereco_completo(address):
    """
    Valida se o endereço está completo e tem CEP válido
    Retorna: (bool, str) - (é_válido, mensagem_erro)
    """
    campos_obrigatorios = {
        'street': 'Rua',
        'number': 'Número',
        'neighborhood': 'Bairro',
        'city': 'Cidade',
        'state': 'Estado',
        'zipcode': 'CEP'
    }
    
    for campo, nome in campos_obrigatorios.items():
        valor = getattr(address, campo, None)
        if not valor or (isinstance(valor, str) and not valor.strip()):
            return False, f"{nome} é obrigatório no endereço"
    
    cep = address.zipcode
    cep_limpo = re.sub(r'[^0-9]', '', cep)
    
    if len(cep_limpo) != 8:
        return False, "CEP inválido no endereço selecionado"
    
    ceps_invalidos = [
        '00000000', '11111111', '22222222', '33333333', 
        '44444444', '55555555', '66666666', '77777777', 
        '88888888', '99999999'
    ]
    
    if cep_limpo in ceps_invalidos:
        return False, "CEP inválido no endereço selecionado"
    
    return True, "OK"

@method_decorator(ratelimit_create_order, name='dispatch')
class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = self.request.user
        
        try:
            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)
            
            if not cart_items.exists():
                raise ValidationError({
                    'detail': 'Seu carrinho está vazio.'
                })
                
        except Cart.DoesNotExist:
            raise ValidationError({
                'detail': 'Carrinho não encontrado.'
            })
        
        address = serializer.validated_data.get('address')
        
        if not address:
            raise ValidationError({
                'address': 'Endereço é obrigatório para criar o pedido.'
            })
        
        if address.user != user:
            log_security_event(
                event_type='UNAUTHORIZED_ADDRESS_ACCESS',
                request=request,
                user=user,
                details=f'Tentativa de usar endereço #{address.id} de outro usuário',
                level='warning'
            )
            raise ValidationError({
                'address': 'Este endereço não pertence a você.'
            })
        
        endereco_valido, mensagem = validar_endereco_completo(address)
        
        if not endereco_valido:
            logger.warning(
                f"[ORDER] Endereço incompleto para usuário {user.id}: {mensagem}"
            )
            raise ValidationError({
                'address': mensagem
            })
        
        shipping_cost = serializer.validated_data.get('shipping_cost', 0)
        shipping_service = serializer.validated_data.get('shipping_service', '')
        shipping_carrier = serializer.validated_data.get('shipping_carrier', '')
        estimated_delivery_days = serializer.validated_data.get('estimated_delivery_days', None)

        if not shipping_cost or shipping_cost <= 0:
            raise ValidationError({
                'shipping_cost': 'Custo de frete é obrigatório e deve ser maior que zero.'
            })
        
        if not shipping_carrier:
            raise ValidationError({
                'shipping_carrier': 'Transportadora é obrigatória.'
            })

        with transaction.atomic():
            products_total = sum(
                item.product.price * item.quantity 
                for item in cart_items
            )

            order = serializer.save(
                client=user, 
                total=products_total, 
                shipping_cost=shipping_cost
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            estimated_delivery_date = None
            if estimated_delivery_days:
                estimated_delivery_date = (
                    datetime.now() + timedelta(days=estimated_delivery_days)
                ).date()

            Shipping.objects.create(
                order=order,
                cost=shipping_cost,
                carrier=shipping_carrier,
                estimated_delivery=estimated_delivery_date,
                status='pending'
            )

            cart_items.delete()
            
            logger.info(
                f"[ORDER] Pedido #{order.id} criado com sucesso para "
                f"usuário {user.id}, CEP {address.zipcode}"
            )
        
        final_serializer = OrderSerializer(order, context={'request': request})
        headers = self.get_success_headers(final_serializer.data)
        
        return Response(
            final_serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering = ['-created_at']

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user)

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user)
    

class OrderCancelView(generics.UpdateAPIView):
    """Endpoint para cancelar pedido - apenas o próprio usuário pode cancelar seus pedidos"""
    serializer_class = OrderStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user)

    def perform_update(self, serializer):
        order = self.get_object()
        
        # Só permite cancelar pedidos pendentes ou processando
        if order.status not in ['pending', 'processing']:
            raise ValidationError(
                "Este pedido não pode ser cancelado. "
                f"Status atual: {order.get_status_display()}"
            )
        
        log_security_event(
            event_type='ORDER_CANCELED',
            request=self.request,
            user=self.request.user,
            details=f'Pedido #{order.id} cancelado pelo usuário',
            level='info'
        )
        
        serializer.save()


class OrderStatusUpdateView(generics.UpdateAPIView):
    """Endpoint para admin atualizar status - APENAS PARA ADMIN"""
    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'
