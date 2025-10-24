# orders/api_views.py
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer, OrderStatusSerializer, OrderSerializer
from cart.models import Cart, CartItem
from accounts.models import Address

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
                raise ValidationError({'detail': 'Seu carrinho está vazio.'})
        except Cart.DoesNotExist:
            raise ValidationError({'detail': 'Carrinho não encontrado.'})

        with transaction.atomic():
            total = sum(item.product.price * item.quantity for item in cart_items)

            order = serializer.save(client=user, total=total)

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            cart_items.delete()
        
        final_serializer = OrderSerializer(order, context={'request': request})
        headers = self.get_success_headers(final_serializer.data)
        return Response(final_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering = ['-created_at']

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user).prefetch_related('orderitem_set')

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
        
        serializer.save()


class OrderStatusUpdateView(generics.UpdateAPIView):
    """Endpoint para admin atualizar status - APENAS PARA ADMIN"""
    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'
