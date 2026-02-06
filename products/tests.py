from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from .filters import ProductFilterSet
from .models import Category, Essence, Product, ProductCustomization, Size
from .serializers import CategorySerializer, ProductSerializer


class CategoryModelTests(TestCase):
	def test_slug_is_generated(self):
		category = Category.objects.create(name='Velas Decorativas')
		self.assertEqual(category.slug, 'velas-decorativas')

	def test_str(self):
		category = Category.objects.create(name='Aromas')
		self.assertEqual(str(category), 'Aromas')

	def test_slug_unique_constraint(self):
		Category.objects.create(name='Velas Casa')
		with self.assertRaises(IntegrityError):
			Category.objects.create(name='Velas Casa')


class EssenceModelTests(TestCase):
	def test_slug_is_generated(self):
		category = Category.objects.create(name='Categorias')
		essence = Essence.objects.create(
			name='Lavanda',
			sensory_profile='Relaxante',
			notes='Floral',
			ambient='Quarto'
		)
		essence.categories.add(category)
		self.assertEqual(essence.slug, 'lavanda')

	def test_str(self):
		category = Category.objects.create(name='Aromas')
		essence = Essence.objects.create(
			name='Baunilha',
			sensory_profile='Doce',
			notes='Gourmet',
			ambient='Sala'
		)
		essence.categories.add(category)
		self.assertEqual(str(essence), 'Baunilha')

	def test_slug_not_overwritten(self):
		category = Category.objects.create(name='Aromas')
		essence = Essence.objects.create(
			name='Limao',
			sensory_profile='Citrico',
			notes='Fresco',
			ambient='Sala',
			slug='essencia-personalizada'
		)
		essence.categories.add(category)
		self.assertEqual(essence.slug, 'essencia-personalizada')


class SizeModelTests(TestCase):
	def test_str(self):
		size = Size.objects.create(name='P', weight=100, unit='g')
		self.assertEqual(str(size), 'P - 100 g')


class ProductModelTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(name='Velas')
		self.size = Size.objects.create(name='M', weight=200, unit='g')

	def test_slug_is_unique(self):
		Product.objects.create(
			name='Vela Classica',
			price=Decimal('20.00'),
			stock_quantity=5,
			category=self.category,
			size=self.size
		)
		product2 = Product.objects.create(
			name='Vela Classica',
			price=Decimal('22.00'),
			stock_quantity=3,
			category=self.category,
			size=self.size
		)
		self.assertEqual(product2.slug, 'vela-classica-1')

	def test_str(self):
		product = Product.objects.create(
			name='Vela Premium',
			price=Decimal('30.00'),
			stock_quantity=2,
			category=self.category,
			size=self.size
		)
		self.assertEqual(str(product), 'Vela Premium')

	def test_slug_not_overwritten(self):
		product = Product.objects.create(
			name='Vela Glow',
			price=Decimal('25.00'),
			stock_quantity=2,
			category=self.category,
			size=self.size,
			slug='vela-custom'
		)
		self.assertEqual(product.slug, 'vela-custom')


class ProductCustomizationModelTests(TestCase):
	def test_str(self):
		category = Category.objects.create(name='Velas')
		customization = ProductCustomization.objects.create(
			category=category,
			name='Gravar Nome',
			instruction='Digite o nome'
		)
		self.assertEqual(str(customization), 'Gravar Nome - Velas')


class ProductFilterSetTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(name='Velas')
		self.size = Size.objects.create(name='M', weight=200, unit='g')
		Product.objects.create(
			name='Produto A',
			price=Decimal('10.00'),
			stock_quantity=5,
			category=self.category,
			size=self.size,
			is_active=True
		)
		Product.objects.create(
			name='Produto B',
			price=Decimal('50.00'),
			stock_quantity=5,
			category=self.category,
			size=self.size,
			is_active=False
		)

	def test_filter_min_price_and_active(self):
		qs = Product.objects.all()
		f = ProductFilterSet(data={'min_price': '20.00'}, queryset=qs)
		results = f.qs
		self.assertEqual(results.count(), 0)


class ProductSerializerTests(TestCase):
	def test_category_image_absolute_url(self):
		image = SimpleUploadedFile('cat.jpg', b'filecontent', content_type='image/jpeg')
		category = Category.objects.create(name='Velas', image=image)

		factory = APIRequestFactory()
		request = factory.get('/api/product/categories/')

		serializer = CategorySerializer(category, context={'request': request})
		self.assertIn('/media/', serializer.data['image'])

	def test_product_image_absolute_url(self):
		image = SimpleUploadedFile('prod.jpg', b'filecontent', content_type='image/jpeg')
		category = Category.objects.create(name='Velas')
		size = Size.objects.create(name='M', weight=200, unit='g')
		product = Product.objects.create(
			name='Vela',
			price=Decimal('10.00'),
			stock_quantity=1,
			category=category,
			size=size,
			image=image
		)

		factory = APIRequestFactory()
		request = factory.get('/api/product/products/')

		serializer = ProductSerializer(product, context={'request': request})
		self.assertIn('/media/', serializer.data['image'])


class ProductApiTests(TestCase):
	def setUp(self):
		self.client_api = APIClient()
		self.category = Category.objects.create(name='Velas')
		self.size = Size.objects.create(name='M', weight=200, unit='g')
		self.essence = Essence.objects.create(
			name='Lavanda',
			sensory_profile='Relaxante',
			notes='Floral',
			ambient='Sala'
		)
		self.essence.categories.add(self.category)
		self.customization = ProductCustomization.objects.create(
			category=self.category,
			name='Gravar Nome',
			instruction='Digite o nome'
		)
		self.product = Product.objects.create(
			name='Vela Premium',
			price=Decimal('30.00'),
			stock_quantity=2,
			category=self.category,
			size=self.size
		)

	def test_product_retrieve_returns_available_options(self):
		url = reverse('product-detail', kwargs={'slug': self.product.slug})
		response = self.client_api.get(url)

		self.assertEqual(response.status_code, 200)
		self.assertIn('available_options', response.data)
		self.assertIn('sizes', response.data['available_options'])
		self.assertIn('essences', response.data['available_options'])
		self.assertIn('customizations', response.data['available_options'])
