from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import CustomUser
from products.models import Category, Essence, Product, ProductCustomization, Size
from .models import Cart, CartItem, CartItemCustomization
from .serializers import CartItemSerializer
from .utils import calcular_frete_melhor_envio, verificar_disponibilidade_retirada


class CartModelTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			email='cart@example.com',
			password='testpass123',
			first_name='Bruno',
			last_name='Silva'
		)
		self.category = Category.objects.create(name='Velas')
		self.size = Size.objects.create(name='G', weight=300, unit='g')
		self.product = Product.objects.create(
			name='Vela Teste',
			price=Decimal('20.00'),
			stock_quantity=10,
			category=self.category,
			size=self.size
		)
		self.essence = Essence.objects.create(
			name='Canela',
			sensory_profile='Quente',
			notes='Especiada',
			ambient='Sala'
		)
		self.essence.categories.add(self.category)

	def test_cart_total(self):
		cart = Cart.objects.create(user=self.user)
		CartItem.objects.create(
			cart=cart,
			product=self.product,
			essence=self.essence,
			quantity=2
		)
		self.assertEqual(cart.get_total(), Decimal('40.00'))

	def test_cart_item_prices_with_customization(self):
		cart = Cart.objects.create(user=self.user)
		item = CartItem.objects.create(
			cart=cart,
			product=self.product,
			essence=self.essence,
			quantity=2
		)
		customization = ProductCustomization.objects.create(
			category=self.category,
			name='Gravar Nome',
			price_extra=Decimal('3.00')
		)
		CartItemCustomization.objects.create(
			cart_item=item,
			option=customization,
			value='Balm'
		)

		self.assertEqual(item.unit_price, Decimal('23.00'))
		self.assertEqual(item.total_price, Decimal('46.00'))

	def test_customization_free_above_quantity(self):
		cart = Cart.objects.create(user=self.user)
		item = CartItem.objects.create(
			cart=cart,
			product=self.product,
			essence=self.essence,
			quantity=3
		)
		customization = ProductCustomization.objects.create(
			category=self.category,
			name='Adesivo',
			price_extra=Decimal('2.00'),
			free_above_quantity=3
		)
		cart_customization = CartItemCustomization.objects.create(
			cart_item=item,
			option=customization,
			value='Sim'
		)

		self.assertEqual(cart_customization.get_cost(item.quantity), 0)


class CartItemSerializerTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(name='Velas')
		self.size = Size.objects.create(name='G', weight=300, unit='g')
		self.product = Product.objects.create(
			name='Vela Teste',
			price=Decimal('20.00'),
			stock_quantity=10,
			category=self.category,
			size=self.size
		)
		self.essence = Essence.objects.create(
			name='Canela',
			sensory_profile='Quente',
			notes='Especiada',
			ambient='Sala'
		)

	def test_requires_essence_when_category_has_essences(self):
		self.essence.categories.add(self.category)

		serializer = CartItemSerializer(data={
			'product_id': self.product.id,
			'quantity': 1
		})

		self.assertFalse(serializer.is_valid())
		self.assertIn('essence_id', serializer.errors)

	def test_rejects_essence_not_in_category(self):
		other_category = Category.objects.create(name='Aromas')
		self.essence.categories.add(other_category)

		serializer = CartItemSerializer(data={
			'product_id': self.product.id,
			'essence_id': self.essence.id,
			'quantity': 1
		})

		self.assertFalse(serializer.is_valid())
		self.assertIn('essence_id', serializer.errors)

	def test_rejects_essence_when_category_has_none(self):
		serializer = CartItemSerializer(data={
			'product_id': self.product.id,
			'essence_id': self.essence.id,
			'quantity': 1
		})

		self.assertFalse(serializer.is_valid())
		self.assertIn('essence_id', serializer.errors)


class CartUtilsTests(TestCase):
	@patch('cart.utils.requests.post')
	@patch('cart.utils.config')
	def test_calcular_frete_melhor_envio_success(self, config_mock, post_mock):
		config_mock.return_value = 'token'
		post_mock.return_value.status_code = 200
		post_mock.return_value.json.return_value = [{'id': 1, 'price': 10}]

		result = calcular_frete_melhor_envio(
			cep_origem='93800192',
			cep_destino='93800192',
			product_list=[{'weight': 1, 'width': 1, 'height': 1, 'length': 1, 'quantity': 1}]
		)

		self.assertEqual(result, [{'id': 1, 'price': 10}])

	@patch('cart.utils.requests.post')
	@patch('cart.utils.config')
	def test_calcular_frete_melhor_envio_error(self, config_mock, post_mock):
		config_mock.return_value = 'token'
		post_mock.return_value.status_code = 400
		post_mock.return_value.text = 'error'

		with self.assertRaises(Exception):
			calcular_frete_melhor_envio(
				cep_origem='93800192',
				cep_destino='93800192',
				product_list=[{'weight': 1, 'width': 1, 'height': 1, 'length': 1, 'quantity': 1}]
			)

	@patch('cart.utils.requests.get')
	def test_verificar_disponibilidade_retirada(self, get_mock):
		get_mock.return_value.status_code = 200
		get_mock.return_value.json.return_value = {'city': 'SAPIRANGA'}

		available, message = verificar_disponibilidade_retirada('93800-192')

		self.assertTrue(available)
		self.assertIn('Retirada', message)


class CartApiTests(TestCase):
	def setUp(self):
		self.client_api = APIClient()
		self.user = CustomUser.objects.create_user(
			email='cartapi@example.com',
			password='testpass123',
			first_name='Ana',
			last_name='Silva'
		)
		self.category = Category.objects.create(name='Velas')
		self.size = Size.objects.create(name='M', weight=200, unit='g')
		self.product = Product.objects.create(
			name='Vela Teste',
			price=Decimal('20.00'),
			stock_quantity=10,
			category=self.category,
			size=self.size
		)

	def test_add_item_success(self):
		self.client_api.force_authenticate(user=self.user)
		url = reverse('cart-item-add')
		response = self.client_api.post(url, {
			'product_id': self.product.id,
			'quantity': 1
		})

		self.assertEqual(response.status_code, 201)
		self.assertEqual(CartItem.objects.count(), 1)

	def test_add_item_requires_essence_when_category_has_one(self):
		essence = Essence.objects.create(
			name='Canela',
			sensory_profile='Quente',
			notes='Especiada',
			ambient='Sala'
		)
		essence.categories.add(self.category)

		self.client_api.force_authenticate(user=self.user)
		url = reverse('cart-item-add')
		response = self.client_api.post(url, {
			'product_id': self.product.id,
			'quantity': 1
		})

		self.assertEqual(response.status_code, 400)

	def test_calculate_shipping_invalid_cep(self):
		self.client_api.force_authenticate(user=self.user)
		url = reverse('calculate-shipping')
		response = self.client_api.post(url, {'cep': '00000000'})

		self.assertEqual(response.status_code, 400)

	def test_calculate_shipping_empty_cart(self):
		self.client_api.force_authenticate(user=self.user)
		url = reverse('calculate-shipping')
		response = self.client_api.post(url, {'cep': '93800192'})

		self.assertEqual(response.status_code, 400)

	@patch('apis.cart_api.cart_api_view.calcular_frete_melhor_envio')
	@patch('apis.cart_api.cart_api_view.verificar_disponibilidade_retirada')
	def test_calculate_shipping_success(self, retirada_mock, frete_mock):
		Cart.objects.create(user=self.user)
		CartItem.objects.create(
			cart=Cart.objects.get(user=self.user),
			product=self.product,
			essence=None,
			quantity=1
		)
		retirada_mock.return_value = False
		frete_mock.return_value = [
			{'id': 1, 'name': 'PAC', 'price': 10, 'delivery_time': 5, 'company': {'name': 'Correios'}}
		]

		self.client_api.force_authenticate(user=self.user)
		url = reverse('calculate-shipping')
		response = self.client_api.post(url, {'cep': '93800-192'})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
