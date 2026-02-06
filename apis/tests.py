from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Address, CustomUser


class ClientsApiTests(TestCase):
	def setUp(self):
		self.client_api = APIClient()
		self.user = CustomUser.objects.create_user(
			email='client@example.com',
			password='testpass123',
			first_name='Ana',
			last_name='Silva'
		)

	@patch('apis.clients_api.clients_api_view.send_verification_email')
	def test_register_sends_verification_email(self, send_mock):
		send_mock.return_value = True
		url = reverse('user-register')
		response = self.client_api.post(url, {
			'first_name': 'Joao',
			'last_name': 'Souza',
			'email': 'novo@example.com',
			'password': 'testpass123',
			'password2': 'testpass123'
		})

		self.assertEqual(response.status_code, 201)
		self.assertTrue(CustomUser.objects.filter(email='novo@example.com').exists())
		send_mock.assert_called_once()

	def test_login_blocks_unverified_email(self):
		url = reverse('token_obtain_pair')
		response = self.client_api.post(url, {
			'email': self.user.email,
			'password': 'testpass123'
		})

		self.assertEqual(response.status_code, 403)
		self.assertIn('error', response.data)

	def test_login_allows_verified_email(self):
		self.user.email_verified = True
		self.user.save(update_fields=['email_verified'])
		url = reverse('token_obtain_pair')
		response = self.client_api.post(url, {
			'email': self.user.email,
			'password': 'testpass123'
		})

		self.assertEqual(response.status_code, 200)

	def test_refresh_requires_cookie(self):
		url = reverse('token_refresh')
		response = self.client_api.post(url)

		self.assertEqual(response.status_code, 401)

	def test_verify_email_success(self):
		self.user.email_verification_token = 'token123'
		self.user.email_verification_sent_at = timezone.now()
		self.user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])

		url = reverse('verify-email')
		response = self.client_api.post(url, {'token': 'token123'})

		self.assertEqual(response.status_code, 200)
		self.user.refresh_from_db()
		self.assertTrue(self.user.email_verified)

	def test_verify_email_expired(self):
		self.user.email_verification_token = 'token-exp'
		self.user.email_verification_sent_at = timezone.now() - timedelta(hours=30)
		self.user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])

		url = reverse('verify-email')
		response = self.client_api.post(url, {'token': 'token-exp'})

		self.assertEqual(response.status_code, 400)
		self.assertIn('expired', response.data)

	@patch('apis.clients_api.clients_api_view.send_verification_email')
	def test_resend_verification_recently_sent(self, send_mock):
		self.user.email_verification_sent_at = timezone.now() - timedelta(minutes=2)
		self.user.save(update_fields=['email_verification_sent_at'])

		url = reverse('resend-verification')
		response = self.client_api.post(url, {'email': self.user.email})

		self.assertEqual(response.status_code, 429)
		send_mock.assert_not_called()

	@patch('apis.clients_api.clients_api_view.send_verification_email')
	def test_resend_verification_success(self, send_mock):
		send_mock.return_value = True
		self.user.email_verification_sent_at = timezone.now() - timedelta(minutes=10)
		self.user.save(update_fields=['email_verification_sent_at'])

		url = reverse('resend-verification')
		response = self.client_api.post(url, {'email': self.user.email})

		self.assertEqual(response.status_code, 200)
		send_mock.assert_called_once()

	def test_address_create_assigns_user(self):
		self.client_api.force_authenticate(user=self.user)
		url = reverse('address-create')
		response = self.client_api.post(url, {
			'street': 'Rua X',
			'number': '10',
			'neighborhood': 'Centro',
			'city': 'Sapiranga',
			'state': 'RS',
			'zipcode': '93800-192'
		})

		self.assertEqual(response.status_code, 201)
		self.assertEqual(Address.objects.count(), 1)
		self.assertEqual(Address.objects.first().user, self.user)

	def test_user_detail_requires_auth(self):
		url = reverse('user_detail')
		response = self.client_api.get(url)

		self.assertEqual(response.status_code, 401)

	def test_user_detail_success(self):
		self.client_api.force_authenticate(user=self.user)
		url = reverse('user_detail')
		response = self.client_api.get(url)

		self.assertEqual(response.status_code, 200)
