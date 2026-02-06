from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from accounts.models import CustomUser

from .models import HeroSection
from .serializers import HeroSectionPublicSerializer


class HeroSectionModelTests(TestCase):
	def test_str(self):
		image = SimpleUploadedFile(
			'hero.jpg',
			b'filecontent',
			content_type='image/jpeg'
		)
		hero = HeroSection.objects.create(
			title='Banner Principal',
			subtitle='Subtitulo',
			button_text='Comprar',
			button_link='/produtos',
			background_image=image,
			is_active=True
		)

		self.assertEqual(str(hero), 'Banner Principal')

	def test_ordering_by_is_active(self):
		image = SimpleUploadedFile(
			'hero2.jpg',
			b'filecontent',
			content_type='image/jpeg'
		)
		inactive = HeroSection.objects.create(
			title='Inativo',
			subtitle='Subtitulo',
			button_text='Comprar',
			button_link='/produtos',
			background_image=image,
			is_active=False
		)
		active = HeroSection.objects.create(
			title='Ativo',
			subtitle='Subtitulo',
			button_text='Comprar',
			button_link='/produtos',
			background_image=image,
			is_active=True
		)

		first = HeroSection.objects.first()
		self.assertEqual(first.id, active.id)


class HeroSectionSerializerTests(TestCase):
	def test_public_serializer_background_image_url(self):
		image = SimpleUploadedFile(
			'hero3.jpg',
			b'filecontent',
			content_type='image/jpeg'
		)
		hero = HeroSection.objects.create(
			title='Hero',
			subtitle='Sub',
			button_text='Comprar',
			button_link='/produtos',
			background_image=image,
			is_active=True
		)

		factory = APIRequestFactory()
		request = factory.get('/api/site-config/hero/')

		serializer = HeroSectionPublicSerializer(hero, context={'request': request})
		self.assertIn('/media/', serializer.data['background_image_url'])


class HeroSectionApiTests(TestCase):
	def setUp(self):
		self.client_api = APIClient()
		self.admin = CustomUser.objects.create_superuser(
			email='admin@example.com',
			password='testpass123',
			first_name='Admin',
			last_name='User'
		)

	def test_public_hero_returns_404_when_missing(self):
		url = reverse('hero-public')
		response = self.client_api.get(url)

		self.assertEqual(response.status_code, 404)

	def test_activate_hero_sets_active(self):
		image = SimpleUploadedFile('hero4.jpg', b'filecontent', content_type='image/jpeg')
		inactive = HeroSection.objects.create(
			title='Inativo',
			subtitle='Sub',
			button_text='Comprar',
			button_link='/produtos',
			background_image=image,
			is_active=False
		)
		active = HeroSection.objects.create(
			title='Ativo',
			subtitle='Sub',
			button_text='Comprar',
			button_link='/produtos',
			background_image=image,
			is_active=True
		)

		self.client_api.force_authenticate(user=self.admin)
		url = reverse('hero-activate', kwargs={'pk': inactive.id})
		response = self.client_api.post(url)

		self.assertEqual(response.status_code, 200)
		inactive.refresh_from_db()
		active.refresh_from_db()
		self.assertTrue(inactive.is_active)
		self.assertFalse(active.is_active)
