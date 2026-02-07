from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Address, CustomUser
from orders.models import Order, OrderItem
from products.models import Category, Product, Size
from .models import Coupon, Payment, Shipping
from .utils import limpar_cpf, validar_cpf, obter_service_id_do_nome, gerar_etiqueta_melhor_envio


class CouponModelTests(TestCase):
	def test_str(self):
		coupon = Coupon.objects.create(
			code='PROMO10',
			discount_percentage=Decimal('10.00'),
			valid_from=timezone.now() - timedelta(days=1),
			valid_until=timezone.now() + timedelta(days=1)
		)
		self.assertEqual(str(coupon), 'PROMO10 - 10.00%')

	def test_is_valid(self):
		coupon = Coupon.objects.create(
			code='PROMO5',
			discount_percentage=Decimal('5.00'),
			valid_from=timezone.now() - timedelta(days=1),
			valid_until=timezone.now() + timedelta(days=1),
			minimum_purchase=Decimal('10.00')
		)
		is_valid, _ = coupon.is_valid(order_total=Decimal('20.00'))
		self.assertTrue(is_valid)

	def test_is_valid_inactive(self):
		coupon = Coupon.objects.create(
			code='OFF',
			discount_percentage=Decimal('5.00'),
			is_active=False,
			valid_from=timezone.now() - timedelta(days=1),
			valid_until=timezone.now() + timedelta(days=1)
		)
		is_valid, message = coupon.is_valid(order_total=Decimal('20.00'))
		self.assertFalse(is_valid)
		self.assertEqual(message, 'Cupom inativo')

	def test_is_valid_expired(self):
		coupon = Coupon.objects.create(
			code='OLD',
			discount_percentage=Decimal('5.00'),
			valid_from=timezone.now() - timedelta(days=10),
			valid_until=timezone.now() - timedelta(days=1)
		)
		is_valid, message = coupon.is_valid(order_total=Decimal('20.00'))
		self.assertFalse(is_valid)
		self.assertEqual(message, 'Cupom expirado')

	def test_is_valid_usage_limit(self):
		coupon = Coupon.objects.create(
			code='LIMIT',
			discount_percentage=Decimal('5.00'),
			valid_from=timezone.now() - timedelta(days=1),
			valid_until=timezone.now() + timedelta(days=1),
			usage_limit=1,
			times_used=1
		)
		is_valid, message = coupon.is_valid(order_total=Decimal('20.00'))
		self.assertFalse(is_valid)
		self.assertEqual(message, 'Cupom atingiu o limite de uso')

	def test_is_valid_minimum_purchase(self):
		coupon = Coupon.objects.create(
			code='MIN',
			discount_percentage=Decimal('5.00'),
			valid_from=timezone.now() - timedelta(days=1),
			valid_until=timezone.now() + timedelta(days=1),
			minimum_purchase=Decimal('50.00')
		)
		is_valid, message = coupon.is_valid(order_total=Decimal('20.00'))
		self.assertFalse(is_valid)
		self.assertIn('Valor mínimo de compra', message)

	def test_calculate_discount(self):
		coupon = Coupon.objects.create(
			code='PROMO10',
			discount_percentage=Decimal('10.00'),
			valid_from=timezone.now() - timedelta(days=1),
			valid_until=timezone.now() + timedelta(days=1)
		)
		discount = coupon.calculate_discount(Decimal('100.00'))
		self.assertEqual(discount, 10.0)


class ShippingPaymentModelTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			email='pay@example.com',
			password='testpass123',
			first_name='Maria',
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
		category = Category.objects.create(name='Velas')
		product = Product.objects.create(
			name='Vela Teste',
			price=Decimal('15.00'),
			stock_quantity=10,
			category=category
		)
		self.order = Order.objects.create(
			client=self.user,
			address=self.address,
			total=product.price,
			shipping_cost=Decimal('5.00')
		)

	def test_shipping_str(self):
		shipping = Shipping.objects.create(order=self.order, cost=Decimal('5.00'))
		self.assertIn('Envio #', str(shipping))

	def test_payment_str(self):
		payment = Payment.objects.create(
			order=self.order,
			method='MERCADOPAGO',
			status='pending'
		)
		self.assertIn('Pagamento #', str(payment))


class CheckoutUtilsTests(TestCase):
	def test_validar_cpf(self):
		self.assertTrue(validar_cpf('39053344705'))
		self.assertFalse(validar_cpf('11111111111'))

	def test_limpar_cpf(self):
		self.assertEqual(limpar_cpf('390.533.447-05'), '39053344705')

	@patch('checkout.utils.requests.post')
	def test_obter_service_id_do_nome(self, post_mock):
		post_mock.return_value.status_code = 200
		post_mock.return_value.json.return_value = [
			{'id': 1, 'name': 'PAC', 'price': '10.00'},
			{'id': 2, 'name': 'SEDEX', 'price': '20.00'},
		]

		service_id = obter_service_id_do_nome(
			service_name='PAC',
			from_postal_code='93800192',
			to_postal_code='93800192',
			package={'weight': 1, 'height': 2, 'width': 2, 'length': 2},
			insurance_value=10,
			access_token='token'
		)

		self.assertEqual(service_id, '1')

	def test_gerar_etiqueta_melhor_envio_invalid_cpf(self):
		user = CustomUser.objects.create_user(
			email='cpf@example.com',
			password='testpass123',
			first_name='Ana',
			last_name='Silva'
		)
		address = Address.objects.create(
			user=user,
			street='Rua F',
			number='12',
			neighborhood='Centro',
			city='Sapiranga',
			state='RS',
			zipcode='93800-192'
		)
		category = Category.objects.create(name='Velas')
		size = Size.objects.create(name='M', weight=200, unit='g')
		product = Product.objects.create(
			name='Vela',
			price=Decimal('10.00'),
			stock_quantity=5,
			category=category,
			size=size
		)
		order = Order.objects.create(
			client=user,
			address=address,
			total=product.price,
			shipping_cost=Decimal('5.00')
		)
		OrderItem.objects.create(
			order=order,
			product=product,
			quantity=1,
			price=product.price
		)
		Shipping.objects.create(order=order, cost=Decimal('5.00'), carrier='PAC')

		user.cpf = '11111111111'
		user.save(update_fields=['cpf'])

		with self.assertRaises(Exception):
			gerar_etiqueta_melhor_envio(order)

	@patch('checkout.utils.obter_service_id_do_nome')
	@patch('checkout.utils.requests.post')
	@patch.dict('os.environ', {'FRETE_API_KEY': 'token'})
	def test_gerar_etiqueta_melhor_envio_success(self, post_mock, service_mock):
		user = CustomUser.objects.create_user(
			email='label@example.com',
			password='testpass123',
			first_name='Ana',
			last_name='Silva'
		)
		user.cpf = '39053344705'
		user.save(update_fields=['cpf'])

		address = Address.objects.create(
			user=user,
			street='Rua F',
			number='12',
			neighborhood='Centro',
			city='Sapiranga',
			state='RS',
			zipcode='93800-192'
		)
		category = Category.objects.create(name='Velas')
		size = Size.objects.create(name='M', weight=200, unit='g')
		product = Product.objects.create(
			name='Vela',
			price=Decimal('10.00'),
			stock_quantity=5,
			category=category,
			size=size
		)
		order = Order.objects.create(
			client=user,
			address=address,
			total=product.price,
			shipping_cost=Decimal('5.00')
		)
		OrderItem.objects.create(
			order=order,
			product=product,
			quantity=1,
			price=product.price
		)
		Shipping.objects.create(order=order, cost=Decimal('5.00'), carrier='PAC')

		service_mock.return_value = '1'
		post_mock.side_effect = [
			MagicMock(status_code=201, json=lambda: {'id': 'ME1', 'tracking': 'TRACK'}),
			MagicMock(status_code=200, json=lambda: {}),
			MagicMock(status_code=200, json=lambda: {}),
			MagicMock(status_code=200, json=lambda: {'url': 'http://label.pdf'}),
		]

		result = gerar_etiqueta_melhor_envio(order)

		self.assertEqual(result['tracking_code'], 'TRACK')
		self.assertEqual(result['label_url'], 'http://label.pdf')


class CheckoutApiTests(TestCase):
	def setUp(self):
		self.client_api = APIClient()
		self.user = CustomUser.objects.create_user(
			email='checkout@example.com',
			password='testpass123',
			first_name='Ana',
			last_name='Silva'
		)
		self.address = Address.objects.create(
			user=self.user,
			street='Rua F',
			number='12',
			neighborhood='Centro',
			city='Sapiranga',
			state='RS',
			zipcode='93800-192'
		)
		category = Category.objects.create(name='Velas')
		product = Product.objects.create(
			name='Vela Teste',
			price=Decimal('15.00'),
			stock_quantity=10,
			category=category
		)
		self.order = Order.objects.create(
			client=self.user,
			address=self.address,
			total=product.price,
			shipping_cost=Decimal('5.00')
		)

	def test_validate_coupon(self):
		coupon = Coupon.objects.create(
			code='PROMO10',
			discount_percentage=Decimal('10.00'),
			valid_from=timezone.now() - timedelta(days=1),
			valid_until=timezone.now() + timedelta(days=1)
		)
		self.client_api.force_authenticate(user=self.user)
		url = reverse('validate-coupon')
		response = self.client_api.post(url, {
			'code': coupon.code,
			'order_total': '100.00'
		})

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data['valid'])

	def test_payment_create(self):
		self.client_api.force_authenticate(user=self.user)
		url = reverse('payment-create')

		with patch('apis.checkout_api.checkout_api_view.create_mercadopago_preference') as pref_mock:
			pref_mock.return_value = {
				'payment_url': 'http://example.com',
				'preference_id': 'pref123'
			}
			response = self.client_api.post(url, {'order': self.order.id})

		self.assertEqual(response.status_code, 201)
		self.assertEqual(Payment.objects.count(), 1)

	def test_payment_webhook_approved_sets_processing(self):
		payment = Payment.objects.create(
			order=self.order,
			method='MERCADOPAGO',
			status='pending'
		)
		OrderItem.objects.create(
			order=self.order,
			product=Product.objects.first(),
			quantity=1,
			price=self.order.total
		)

		sdk_mock = MagicMock()
		sdk_mock.payment.return_value.get.return_value = {
			'status': 200,
			'response': {
				'status': 'approved',
				'external_reference': str(self.order.id),
				'payer': {'identification': {'number': '39053344705'}}
			}
		}

		with patch('apis.checkout_api.checkout_api_view.mercadopago.SDK', return_value=sdk_mock):
			url = reverse('payment-webhook')
			response = self.client_api.post(url, {'type': 'payment', 'data': {'id': '123'}}, format='json')

		self.assertEqual(response.status_code, 200)
		self.order.refresh_from_db()
		payment.refresh_from_db()
		self.assertEqual(self.order.status, 'processing')
		self.assertEqual(payment.status, 'approved')

	def test_payment_webhook_records_backorder(self):
		product = Product.objects.first()
		product.stock_quantity = 1
		product.save(update_fields=['stock_quantity'])

		payment = Payment.objects.create(
			order=self.order,
			method='MERCADOPAGO',
			status='pending'
		)
		item = OrderItem.objects.create(
			order=self.order,
			product=product,
			quantity=3,
			price=self.order.total
		)

		sdk_mock = MagicMock()
		sdk_mock.payment.return_value.get.return_value = {
			'status': 200,
			'response': {
				'status': 'approved',
				'external_reference': str(self.order.id),
				'payer': {'identification': {'number': '39053344705'}}
			}
		}

		with patch('apis.checkout_api.checkout_api_view.mercadopago.SDK', return_value=sdk_mock):
			url = reverse('payment-webhook')
			response = self.client_api.post(url, {'type': 'payment', 'data': {'id': '123'}}, format='json')

		self.assertEqual(response.status_code, 200)
		item.refresh_from_db()
		product.refresh_from_db()
		self.assertEqual(item.backorder_quantity, 2)
		self.assertEqual(product.stock_quantity, 0)
