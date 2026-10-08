from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

# Create your tests here.


User = get_user_model()


class AccountsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # پاک‌سازی کش، کدهای تأیید و شمارنده‌های باقی‌مانده از تست قبلی را حذف می‌کند.
        cache.clear()
        self.register_url = '/api/auth/register/'
        self.verify_url = '/api/auth/verify/'
        self.login_url = '/api/auth/login/'
        self.change_password_url = '/api/auth/change-password/'
        self.delete_account_url = '/api/auth/delete-account/'
        self.resend_otp_url = '/api/auth/resend-otp/'
        self.logout_url = '/api/auth/logout/'

        self.test_email = 'test@example.com'
        self.test_password = 'Abcd123!'
        self.test_user_data = {
            'email': self.test_email,
            'first_name': 'علی',
            'last_name': 'رضایی',
            'password': self.test_password,
            'password2': self.test_password,
        }

    @patch('accounts.utils.otp_generate')
    def test_register_success(self, mock_otp):
        mock_otp.return_value = 123456
        response = self.client.post(self.register_url, self.test_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.test_email).exists())
        user = User.objects.get(email=self.test_email)
        self.assertFalse(user.is_active)

    def test_register_duplicate_active_email(self):
        User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        response = self.client.post(self.register_url, self.test_user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('قبلا تایید شده است', response.data['message'])

    def test_register_invalid_email(self):
        data = self.test_user_data.copy()
        data['email'] = 'invalid'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    @patch('accounts.utils.otp_generate')
    @patch('accounts.utils.otp_verify')
    def test_verify_success(self, mock_verify, mock_generate):
        mock_generate.return_value = 123456
        response = self.client.post(self.register_url, self.test_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=self.test_email)
        self.assertFalse(user.is_active)
        mock_verify.return_value = True
        response = self.client.post(self.verify_url, {'email': self.test_email, 'code': '123456'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('تأیید شد', response.data['message'])
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        mock_generate.assert_called_once_with(self.test_email)
        mock_verify.assert_called_once_with(self.test_email, '123456')

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    def test_verify_wrong_code(self):
        with patch('accounts.utils.otp_generate') as mock_gen:
            mock_gen.return_value = 123456
            self.client.post(self.register_url, self.test_user_data)
        response = self.client.post(self.verify_url, {'email': self.test_email, 'code': '000000'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('اشتباه است', response.data['message'])

    def test_verify_already_active(self):
        user = User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        response = self.client.post(self.verify_url, {'email': self.test_email, 'code': '123456'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('قبلا تایید شده', response.data['message'])

    def test_login_success(self):
        user = User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        response = self.client.post(self.login_url, {'email': self.test_email, 'password': self.test_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_login_inactive_user(self):
        User.objects.create_user(email=self.test_email, password=self.test_password, is_active=False)
        response = self.client.post(self.login_url, {'email': self.test_email, 'password': self.test_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('تأیید کنید', response.data['message'])

    def test_login_wrong_password(self):
        User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        response = self.client.post(self.login_url, {'email': self.test_email, 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_success(self):
        user = User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        # احراز هویت مستقیم، سناریوی تغییر رمز را از جریان ورود مستقل می‌کند.
        self.client.force_authenticate(user=user)
        new_pass = 'NewPass456!'
        response = self.client.post(self.change_password_url, {
            'old_password': self.test_password,
            'new_password': new_pass,
            'confirm_password': new_pass
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_pass))

    def test_change_password_wrong_old(self):
        user = User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        self.client.force_authenticate(user=user)
        response = self.client.post(self.change_password_url, {
            'old_password': 'wrong',
            'new_password': 'NewPass456!',
            'confirm_password': 'NewPass456!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('فعلی اشتباه است', response.data['old_password'])

    def test_change_password_mismatch(self):
        user = User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        self.client.force_authenticate(user=user)
        response = self.client.post(self.change_password_url, {
            'old_password': self.test_password,
            'new_password': 'NewPass456!',
            'confirm_password': 'different'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_account_success(self):
        user = User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        self.client.force_authenticate(user=user)
        response = self.client.post(self.delete_account_url, {'password': self.test_password, 'confirm': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(email=self.test_email).exists())
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')

    def test_delete_account_wrong_password(self):
        user = User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        self.client.force_authenticate(user=user)
        response = self.client.post(self.delete_account_url, {'password': 'wrong', 'confirm': True})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(email=self.test_email).exists())

    def test_delete_account_not_confirmed(self):
        user = User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        self.client.force_authenticate(user=user)
        response = self.client.post(self.delete_account_url, {'password': self.test_password, 'confirm': False})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@patch('accounts.utils.otp_generate')
def test_resend_otp_success(self, mock_generate):
    mock_generate.return_value = 654321
    user = User.objects.create_user(email=self.test_email, password=self.test_password, is_active=False)
    from django.core.cache import cache
    cache.clear()
    response = self.client.post(self.resend_otp_url, {'email': self.test_email})
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertIn('کد تأیید جدید', response.data['message'])
    mock_generate.assert_called_once_with(self.test_email)

    def test_resend_otp_already_active(self):
        User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        response = self.client.post(self.resend_otp_url, {'email': self.test_email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        user = User.objects.create_user(email=self.test_email, password=self.test_password, is_active=True)
        self.client.force_authenticate(user=user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies.get('access_token', '').value, '')
