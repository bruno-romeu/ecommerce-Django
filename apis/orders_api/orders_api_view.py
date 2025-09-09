from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import ValidationError
from django.db import transaction

from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer, OrderStatusSerializer
from cart.models import Cart
from accounts.models import CustomUser, Address


# API para criar pedidos a partir do carrinho de compras 
class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        try:
            client = CustomUser.objects.get(user=user)
        except CustomUser.DoesNotExist:
            raise ValidationError({'detail': 'Cliente não encontrado.'})

    # obter o carrinho do usuário
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            # se o carrinho não existe ou está vazio, não pode criar um pedido
            raise ValidationError({'detail':'Carrinho vazio ou não encontrado.'})

        cart_items = cart.items.all()

        if not cart_items.exists():
            raise ValidationError({'detail': 'Carrinho vazio. Adicione itens antes de criar um pedido.'})
        
    # usar transação atômmica para garantir que tudo seja salvo ou nada seja salvo
        with transaction.atomic():
            address = Address.objects.get(id=self.request.data.get('address'))
            order = serializer.save(client=client, address=address)

            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
            cart_items.delete()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)




#API para listar pedidos do usuário autenticado
class OrderListView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer #verificar se o serializer está aninhado
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            client = CustomUser.objects.get(user=user)
            return Order.objects.filter(client=client).order_by('-created_at')
        except CustomUser.DoesNotExist:
            return Order.objects.none()



#API para detalhar um pedido específico do usuário autenticado
class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk' # verificar se o correto é 'pk' ou 'id'

    def get_queryset(self):
        user = self.request.user
        try:
            client = CustomUser.objects.get(user=user)
            return Order.objects.filter(client=client)
        except CustomUser.DoesNotExist:
            return Order.objects.none()
    
    #A combinação de lookup_field e get_queryset garante que: 1) o pedido seja encontrado pelo pk da URL, e 2) ele só seja encontrado se pertencer ao usuário logado. Se não pertencer, resultará em 404 Not Found.


#API para atualizar o status de um pedido específico do usuário autenticado
class OrderStatusUpdateView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'  # verificar se o correto é 'pk' ou 'id'

    def get_queryset(self):
        return Order.objects.all() # o Admin pode alterar o status de qualquer pedido
    
    def perform_update(self, serializer):
        order = self.get_object()
        old_status = order.status
        new_status = self.request.data.get('status')

        if new_status is None or new_status == old_status:
            serializer.save()
            return
        
        if old_status in ['delivered', 'canceled']:
            raise ValidationError({'status': f'Não é possível alterar o status de um pedido já {order.get_status_display()}'})
        
        if new_status == 'paid' and old_status != 'pending':
            raise ValidationError({'status': f'O status "pago" só pode ser definido em um pedido "pendente".'})
        
        if new_status == 'shipped' and old_status != 'paid':
            raise ValidationError({'status': f'O status "enviado" só pode ser definido em um pedido "pago".'})

        if new_status == 'delivered' and old_status != 'shipped':
            raise ValidationError({'status': f'O status "entregue" só pode ser definido em um pedido "enviado".'})

        if new_status == 'canceled' and old_status in ['pending', 'paid']:
            raise ValidationError({'status': f'O status "cancelado" só pode ser definido em um pedido "pendente" ou "pago".'})

        serializer.save()

        # lógica para enviar notificações das atualizações de status
        ...