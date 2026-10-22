from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class AccountsAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_individual_donor_registration(self):
        payload = {
            "email": "testdonor@secondlife.eco",
            "password": "password123",
            "confirm_password": "password123",
            "name": "Test Donor",
            "role": "DONOR",
            "account_type": "INDIVIDUAL",
            "city": "Seattle",
            "preferred_categories": ["clothes", "books"]
        }
        res = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', res.data)
        self.assertIn('access', res.data['tokens'])
        self.assertEqual(res.data['user']['email'], "testdonor@secondlife.eco")
        self.assertEqual(res.data['user']['role'], "DONOR")

    def test_organization_receiver_registration(self):
        payload = {
            "email": "orgrec@secondlife.eco",
            "password": "password123",
            "confirm_password": "password123",
            "name": "Hope Center",
            "role": "RECEIVER",
            "account_type": "ORGANIZATION",
            "organization_name": "Hope Shelter Foundation",
            "organization_type": "SHELTER",
            "license_number": "LIC-9988",
            "city": "Seattle"
        }
        res = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="orgrec@secondlife.eco")
        self.assertFalse(user.is_verified) # Organizations must be verified by admin
        self.assertEqual(user.organization.verification_status, "PENDING")

    def test_login_and_me_endpoint(self):
        user = User.objects.create_user(
            email="loginuser@secondlife.eco",
            password="password123",
            name="Login User",
            role=User.Role.DONOR
        )
        res = self.client.post('/api/auth/login/', {"email": "loginuser@secondlife.eco", "password": "password123"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        token = res.data['tokens']['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        me_res = self.client.get('/api/auth/me/')
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertEqual(me_res.data['email'], "loginuser@secondlife.eco")
