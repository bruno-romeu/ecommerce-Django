from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from accounts.models import Address, CustomUser
from cart.models import Cart, CartItem
from checkout.models import Payment, Shipping
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer, OrderStatusSerializer
from products.models import Category, Product


class OrderModelTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			email='order@example.com',
			password='testpass123',
			first_name='Paula',
			last_name='Lima'
		)
		self.address = Address.objects.create(
			user=self.user,
			street='Rua B',
			number='20',
			neighborhood='Centro',
			city='Sapiranga',
			state='RS',
			zipcode='93800-192'
		)
		self.category = Category.objects.create(name='Velas')
		self.product = Product.objects.create(
			name='Vela Teste',
			price=Decimal('25.00'),
			stock_quantity=10,
			category=self.category
		)

	def test_str(self):
		order = Order.objects.create(
			client=self.user,
			address=self.address,
			total=Decimal('50.00'),
			shipping_cost=Decimal('10.00')
		)
		self.assertIn('Pedido #', str(order))

	def test_total_with_shipping(self):
		order = Order.objects.create(
			client=self.user,
			address=self.address,
			total=Decimal('50.00'),
			shipping_cost=Decimal('10.00')
		)
		self.assertEqual(order.get_total_with_shipping(), Decimal('60.00'))

	def test_order_item_str(self):
		order = Order.objects.create(
			client=self.user,
			address=self.address,
			total=Decimal('50.00'),
			shipping_cost=Decimal('10.00')
		)
		item = OrderItem.objects.create(
			order=order,
			product=self.product,
			quantity=2,
			price=Decimal('25.00')
		)
		self.assertEqual(str(item), '2 x Vela Teste')

	def test_payment_status_without_payment(self):
		order = Order.objects.create(
			client=self.user,
			address=self.address,
			total=Decimal('25.00'),
			shipping_cost=Decimal('5.00')
		)
		self.assertEqual(order.payment_status, 'Sem pagamento')

	def test_shipping_status_without_shipping(self):
		order = Order.objects.create(
			client=self.user,
			address=self.address,
			total=Decimal('25.00'),
			shipping_cost=Decimal('5.00')
		)
		self.assertEqual(order.shipping_status, 'Sem envio')

	def test_payment_and_shipping_status_with_relations(self):
		order = Order.objects.create(
			client=self.user,
			address=self.address,
			total=Decimal('25.00'),
			shipping_cost=Decimal('5.00')
		)
		Payment.objects.create(order=order, method='MERCADOPAGO', status='approved')
		Shipping.objects.create(order=order, cost=Decimal('5.00'), status='processing')

		self.assertEqual(order.payment_status, 'approved')
		self.assertEqual(order.shipping_status, 'processing')


class OrderStatusSerializerTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			email='status@example.com',
			password='testpass123',
			first_name='Rafa',
			last_name='Costa'
		)
		self.address = Address.objects.create(
			user=self.user,
			street='Rua C',
			number='30',
			neighborhood='Centro',
			city='Sapiranga',
			state='RS',
			zipcode='93800-192'
		)

	def test_valid_transition_paid_to_processing(self):
		order = Order.objects.create(
			client=self.user,
			address=self.address,
			status='paid',
			total=Decimal('20.00'),
			shipping_cost=Decimal('5.00')
		)
		serializer = OrderStatusSerializer(order, data={'status': 'processing'})
		self.assertTrue(serializer.is_valid(), serializer.errors)

	def test_invalid_transition_pending_to_shipped(self):
		order = Order.objects.create(
			client=self.user,
			address=self.address,
			status='pending',
			total=Decimal('20.00'),
			shipping_cost=Decimal('5.00')
		)
		serializer = OrderStatusSerializer(order, data={'status': 'shipped'})
		self.assertFalse(serializer.is_valid())


class OrderSerializerTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			email='serializer@example.com',
			password='testpass123',
			first_name='Rafa',
			last_name='Costa'
		)
		self.other_user = CustomUser.objects.create_user(
			email='other@example.com',
			password='testpass123',
			first_name='Lia',
			last_name='Silva'
		)
		self.address = Address.objects.create(
			user=self.other_user,
			street='Rua D',
			number='10',
			neighborhood='Centro',
			city='Sapiranga',
			state='RS',
			zipcode='93800-192'
		)

	def test_validate_address_belongs_to_user(self):
		factory = APIRequestFactory()
		request = factory.post('/api/order/order-create/')
		request.user = self.user

		serializer = OrderSerializer(
			data={'address': self.address.id},
			context={'request': request}
		)

		self.assertFalse(serializer.is_valid())
		self.assertIn('address', serializer.errors)


class OrderApiTests(TestCase):
	def setUp(self):
		self.client_api = APIClient()
		self.user = CustomUser.objects.create_user(
			email='orderapi@example.com',
			password='testpass123',
			first_name='Ana',
			last_name='Silva'
		)
		self.address = Address.objects.create(
			user=self.user,
			street='Rua E',
			number='11',
			neighborhood='Centro',
			city='Sapiranga',
			state='RS',
			zipcode='93800-192'
		)
		self.category = Category.objects.create(name='Velas')
		self.product = Product.objects.create(
			name='Vela Teste',
			price=Decimal('30.00'),
			stock_quantity=10,
			category=self.category
		)

	def test_order_create_requires_cart(self):
		self.client_api.force_authenticate(user=self.user)
		url = reverse('order-create')
		response = self.client_api.post(url, {
			'address': self.address.id,
			'shipping_cost': '10.00',
			'shipping_carrier': 'Correios'
		})

		self.assertEqual(response.status_code, 400)
		self.assertIn('detail', response.data)

	def test_order_create_success(self):
		cart = Cart.objects.create(user=self.user)
		CartItem.objects.create(
			cart=cart,
			product=self.product,
			quantity=2,
			essence=None
		)

		self.client_api.force_authenticate(user=self.user)
		url = reverse('order-create')
		response = self.client_api.post(url, {
			'address': self.address.id,
			'shipping_cost': '10.00',
			'shipping_carrier': 'Correios'
		})

		self.assertEqual(response.status_code, 201)
		self.assertEqual(Order.objects.count(), 1)
		order = Order.objects.first()
		self.assertEqual(order.client, self.user)

	def test_order_cancel_invalid_status(self):
		order = Order.objects.create(
			client=self.user,
			address=self.address,
			status='shipped',
			total=Decimal('30.00'),
			shipping_cost=Decimal('10.00')
		)

		self.client_api.force_authenticate(user=self.user)
		url = reverse('order-cancel', kwargs={'pk': order.id})
		response = self.client_api.patch(url, {'status': 'canceled'})

		self.assertEqual(response.status_code, 400)

	def test_order_cancel_restores_stock_when_paid(self):
		order = Order.objects.create(
			client=self.user,
			address=self.address,
			status='processing',
			total=Decimal('60.00'),
			shipping_cost=Decimal('10.00')
		)
		OrderItem.objects.create(
			order=order,
			product=self.product,
			quantity=2,
			price=Decimal('30.00')
		)
		Payment.objects.create(
			order=order,
			method='MERCADOPAGO',
			status='approved'
		)

		self.product.stock_quantity = 8
		self.product.save(update_fields=['stock_quantity'])

		self.client_api.force_authenticate(user=self.user)
		url = reverse('order-cancel', kwargs={'pk': order.id})
		response = self.client_api.patch(url, {'status': 'canceled'})

		self.assertEqual(response.status_code, 200)
		order.refresh_from_db()
		self.product.refresh_from_db()
		self.assertEqual(order.status, 'canceled')
		self.assertEqual(self.product.stock_quantity, 10)
