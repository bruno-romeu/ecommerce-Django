from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from .models import Address, CustomUser
from .serializers import AddressSerializer, UserClientRegisterSerializer
from .utils import is_verification_token_valid, send_verification_email


class CustomUserModelTests(TestCase):
	def test_str(self):
		user = CustomUser.objects.create_user(
			email='user@example.com',
			password='testpass123',
			first_name='Ana',
			last_name='Silva'
		)

		self.assertEqual(str(user), 'user@example.com')


class AddressModelTests(TestCase):
	def test_str(self):
		user = CustomUser.objects.create_user(
			email='addr@example.com',
			password='testpass123',
			first_name='Joao',
			last_name='Souza'
		)

		address = Address.objects.create(
			user=user,
			street='Rua A',
			number='10',
			neighborhood='Centro',
			city='Sapiranga',
			state='RS',
			zipcode='93800-192'
		)

		self.assertIn('Rua A', str(address))


class CustomUserManagerTests(TestCase):
	def test_create_user_requires_email(self):
		with self.assertRaises(ValueError):
			CustomUser.objects.create_user(
				email='',
				password='testpass123',
				first_name='Ana',
				last_name='Silva'
			)

	def test_create_superuser_requires_flags(self):
		with self.assertRaises(ValueError):
			CustomUser.objects.create_superuser(
				email='admin@example.com',
				password='testpass123',
				is_staff=False,
				is_superuser=True
			)


class AddressSerializerTests(TestCase):
	def test_validate_zipcode_formats(self):
		serializer = AddressSerializer(data={
			'street': 'Rua A',
			'number': '10',
			'neighborhood': 'Centro',
			'city': 'Sapiranga',
			'state': 'RS',
			'zipcode': '93800192'
		})

		self.assertTrue(serializer.is_valid(), serializer.errors)
		self.assertEqual(serializer.validated_data['zipcode'], '93800-192')

	def test_validate_zipcode_invalid(self):
		serializer = AddressSerializer(data={
			'street': 'Rua A',
			'number': '10',
			'neighborhood': 'Centro',
			'city': 'Sapiranga',
			'state': 'RS',
			'zipcode': '00000000'
		})

		self.assertFalse(serializer.is_valid())
		self.assertIn('zipcode', serializer.errors)

	def test_validate_state_uppercase(self):
		serializer = AddressSerializer(data={
			'street': 'Rua A',
			'number': '10',
			'neighborhood': 'Centro',
			'city': 'Sapiranga',
			'state': 'RS',
			'zipcode': '93800192'
		})

		self.assertTrue(serializer.is_valid(), serializer.errors)
		self.assertEqual(serializer.validated_data['state'], 'RS')


class UserClientRegisterSerializerTests(TestCase):
	def test_passwords_must_match(self):
		serializer = UserClientRegisterSerializer(data={
			'first_name': 'Ana',
			'last_name': 'Silva',
			'email': 'ana@example.com',
			'password': 'testpass123',
			'password2': 'mismatch'
		})

		self.assertFalse(serializer.is_valid())
		self.assertIn('password', serializer.errors)

	def test_email_must_be_unique(self):
		CustomUser.objects.create_user(
			email='ana@example.com',
			password='testpass123',
			first_name='Ana',
			last_name='Silva'
		)

		serializer = UserClientRegisterSerializer(data={
			'first_name': 'Ana',
			'last_name': 'Silva',
			'email': 'ana@example.com',
			'password': 'testpass123',
			'password2': 'testpass123'
		})

		self.assertFalse(serializer.is_valid())
		self.assertIn('email', serializer.errors)


class VerificationUtilsTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			email='verify@example.com',
			password='testpass123',
			first_name='Ana',
			last_name='Silva'
		)

	def test_is_verification_token_valid(self):
		self.user.email_verification_sent_at = timezone.now() - timedelta(hours=23)
		self.user.save(update_fields=['email_verification_sent_at'])

		self.assertTrue(is_verification_token_valid(self.user))

		self.user.email_verification_sent_at = timezone.now() - timedelta(hours=25)
		self.user.save(update_fields=['email_verification_sent_at'])

		self.assertFalse(is_verification_token_valid(self.user))

	def test_send_verification_email_generates_token(self):
		with patch('accounts.utils.inngest_client.send', new_callable=Mock) as send_mock, \
			 patch('accounts.utils.async_to_sync', side_effect=lambda f: f):
			result = send_verification_email(self.user)

		self.user.refresh_from_db()
		self.assertTrue(result)
		self.assertIsNotNone(self.user.email_verification_token)
		self.assertIsNotNone(self.user.email_verification_sent_at)
		send_mock.assert_called_once()
