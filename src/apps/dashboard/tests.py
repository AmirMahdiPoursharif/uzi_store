from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class DashboardProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='علی',
            last_name='رضایی',
            is_active=True
        )
        self.client.force_authenticate(user=self.user)
        self.profile_url = '/api/auth/profile/'
        self.update_profile_url = '/api/auth/update-profile/'

    def test_get_profile_success(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['first_name'], self.user.first_name)
        self.assertEqual(response.data['last_name'], self.user.last_name)

    def test_update_profile_success(self):
        data = {
            'first_name': 'محمد',
            'last_name': 'کریمی',
            'email': 'mohammad@example.com'
        }
        response = self.client.put(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'محمد')
        self.assertEqual(self.user.last_name, 'کریمی')
        self.assertEqual(self.user.email, 'mohammad@example.com')

    def test_update_profile_partial(self):
        data = {
            'first_name': 'رضا'
        }
        response = self.client.patch(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'رضا')
        self.assertEqual(self.user.last_name, 'رضایی')

    def test_update_profile_invalid_email(self):
        data = {
            'email': 'invalid-email'
        }
        response = self.client.put(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_profile_duplicate_email(self):
        User.objects.create_user(
            email='other@example.com',
            password='TestPass123!',
            first_name='سارا',
            last_name='احمدی',
            is_active=True
        )
        data = {
            'email': 'other@example.com'
        }
        response = self.client.put(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertTrue(len(response.data['email']) > 0)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_empty_fields(self):
        data = {
            'first_name': '',
            'last_name': ''
        }
        response = self.client.put(self.update_profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        def test_get_profile_after_update(self):
            data = {
                'first_name': 'سعید',
                'last_name': 'محمدی'
            }
            self.client.put(self.update_profile_url, data, format='json')
            response = self.client.get(self.profile_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['first_name'], 'سعید')
            self.assertEqual(response.data['last_name'], 'محمدی')