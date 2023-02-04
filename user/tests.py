from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from django.contrib.auth import get_user_model
from .models import OTP

User = get_user_model()


class UserTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1_data = {
            'email': 'user1@test.com',
            'username': 'user1_for_test',
            'password': 'test_password',
        }
        cls.user2_data = {
            'email': 'user2@test.com',
            'username': 'user2_for_test',
            'password': 'test_password',
        }

    def test_create_user_obj(self):
        user_obj1 = User.objects.create_user(
            email=self.user1_data.get('email'),
            username=self.user1_data.get('username'),
            password=self.user1_data.get('password'),
        )
        user_obj2 = User.objects.create_user(
            email=self.user2_data.get('email'),
            username=self.user2_data.get('username'),
            password=self.user2_data.get('password'),
        )

        self.assertEqual(user_obj1.id, 1)
        self.assertEqual(user_obj1.username, self.user1_data.get('username'))
        self.assertNotEqual(user_obj1.password, self.user1_data.get('password'))
        self.assertTrue(user_obj1.is_active, msg='user object is not active')
        self.assertFalse(user_obj1.is_superuser, msg='user object is superuser')
        self.assertNotEqual(user_obj1.id, user_obj2.id)
        self.assertEqual(user_obj2.email, self.user2_data.get('email'))
        self.assertNotEqual(user_obj2.password, self.user2_data.get('password'))
        self.assertNotEqual(user_obj1.password, user_obj2.password)

    def signup(self, username: str, email: str, password: str, password2: str):
        url = reverse('signup')

        data = {
            'username': username,
            'email': email,
            'password': password,
            'password2': password2,
        }

        response = self.client.post(url, data=data)
        return response.status_code, response.json()

    def test_signup(self):

        """Test signup with acceptable credentials"""

        # User 1
        user1_signup_data = self.user1_data
        user1_signup_data['email'] = user1_signup_data['email'].upper()
        user1_signup_data['password2'] = user1_signup_data['password'] + '!'

        status_code, response_data = self.signup(**user1_signup_data)
        self.assertEqual(status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Password fields didn't match." in response_data.get('password'))

        # User 2
        user2_signup_data = self.user2_data
        user2_signup_data['password2'] = user2_signup_data['password']

        status_code, response_data = self.signup(**user2_signup_data)
        self.assertEqual(status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data.get('username'), user2_signup_data['username'])
        self.assertEqual(response_data.get('email'), user2_signup_data['email'])
        self.assertFalse(response_data.get('is_verified'))
        self.assertTrue('id' in response_data.keys())
        self.assertTrue('tokens' in response_data.keys())

        status_code, response_data = self.signup(**user2_signup_data)
        self.assertEqual(status_code, status.HTTP_400_BAD_REQUEST)

        """Test signup with unacceptable credentials"""

        # User 3
        unacceptable_user_data = {
            'email': 'user1@test.com',
            'username': 'user1@for_test',
            'password': 'test_password',
            'password2': 'test_password',
        }

        status_code, response_data = self.signup(**unacceptable_user_data)
        self.assertEqual(status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('username' in response_data)
        self.assertEqual(
            response_data.get('username')[0],
            'Enter a valid username. This value may contain only letters, numbers, and ./_ characters.',
        )

    def test_login(self):
        login_url = reverse('login')

        user = User.objects.create_user(**self.user1_data)

        user_data = {
            'username': self.user1_data.get('username'),
            'password': self.user1_data.get('password') + '!!',
        }

        login_response = self.client.post(login_url, user_data)
        self.assertEqual(login_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue('detail' in login_response.json().keys())
        self.assertEqual(login_response.json().get('detail'), 'Invalid credentials.')

        user_data['password'] = self.user1_data.get('password')
        login_response = self.client.post(login_url, user_data)
        self.assertEqual(login_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('email' in login_response.json().keys(), msg='Email should be in the response.')
        self.assertEqual(login_response.json().get('email')[0], 'Your email is not verified.')

        user.is_verified = True
        user.save()

        login_response = self.client.post(login_url, user_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        response_dict_keys = login_response.json().keys()
        self.assertTrue('id' in response_dict_keys)
        self.assertTrue('username' in response_dict_keys)
        self.assertTrue('email' in response_dict_keys)
        self.assertTrue('tokens' in response_dict_keys)
        self.assertFalse('password' in response_dict_keys)


class OTPTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_email = 'usER@teSt.com'
        cls.user_username = 'usER@teSt.com'

    def setUp(self) -> None:
        self.user = User.objects.create_user(username=self.user_username, email=self.user_email, password='test1234')
        self.user_access_token = self.user.tokens().get('access')

    def test_create_otp_object(self):
        otp = OTP.generate_otp(self.user)
        self.assertEqual(otp.id, 1)

    def request_otp_api(self, user_id):
        url = reverse('request_otp')
        return self.client.post(
            url, data={'user': user_id},
            **{'HTTP_AUTHORIZATION': f'Bearer {self.user_access_token}'}
        )

    def test_request_otp(self):
        response = self.request_otp_api(self.user.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.request_otp_api(self.user.id)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_verify_otp(self):
        self.request_otp_api(self.user.id)
        otp_code = OTP.objects.filter(user_id=self.user.id).first().code

        url = reverse('verify_otp')

        """Wrong OTP"""
        response = self.client.post(
            url, data={'user_id': self.user.id, 'code': '-----'},
            **{'HTTP_AUTHORIZATION': f'Bearer {self.user_access_token}'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('code' in response.json())
        self.assertFalse(User.objects.get(id=self.user.id).is_verified)

        """Correct OTP"""
        response = self.client.post(
            url, data={'user_id': self.user.id, 'code': otp_code},
            **{'HTTP_AUTHORIZATION': f'Bearer {self.user_access_token}'}
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(User.objects.get(id=self.user.id).is_verified)
