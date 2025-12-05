from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

class AccountTests(APITestCase):
    def test_registration(self):
        url = reverse('auth_register')
        data = {'username': 'testuser', 'password': 'testpassword', 'email': 'test@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')

    def test_login(self):
        User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')
        url = reverse('token_obtain_pair')
        data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_logout(self):
        User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')
        login_url = reverse('token_obtain_pair')
        login_data = {'username': 'testuser', 'password': 'testpassword'}
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']

        logout_url = reverse('auth_logout')
        logout_data = {'refresh': refresh_token}
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        response = self.client.post(logout_url, logout_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_delete_user(self):
        User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')
        login_url = reverse('token_obtain_pair')
        login_data = {'username': 'testuser', 'password': 'testpassword'}
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['access']

        delete_url = reverse('auth_delete')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)

    def test_auth_status(self):
        User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')
        login_url = reverse('token_obtain_pair')
        login_data = {'username': 'testuser', 'password': 'testpassword'}
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['access']

        status_url = reverse('auth_status')
        
        # Test authenticated
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        response = self.client.get(status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

        # Test unauthenticated
        self.client.credentials()
        response = self.client.get(status_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
