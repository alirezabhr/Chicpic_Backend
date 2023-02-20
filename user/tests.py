from django.urls import reverse
from django.utils import timezone
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

    def test_retrieve_user_details(self):
        url = reverse('user_detail')

        user = User.objects.create_user(**self.user1_data)

        response = self.client.get(url, **{'HTTP_AUTHORIZATION': f'Bearer {user.tokens().get("access")}'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_dict_keys = response.json().keys()
        self.assertIn('id', response_dict_keys)
        self.assertIn('username', response_dict_keys)
        self.assertIn('email', response_dict_keys)
        self.assertIn('tokens', response_dict_keys)
        self.assertIn('isVerified', response_dict_keys)
        self.assertNotIn('password', response_dict_keys)
        self.assertIn('userAdditional', response_dict_keys)

    def test_refresh_token(self):
        url = reverse('refresh_token')

        user = User.objects.create_user(**self.user1_data)
        tokens = user.tokens()
        previous_access_token = tokens.get('access')
        previous_refresh_token = tokens.get('refresh')

        response = self.client.post(url, {'refresh': previous_refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Both access and refresh token should change
        self.assertNotEqual(previous_access_token, response.json().get('access'))
        self.assertNotEqual(previous_refresh_token, response.json().get('refresh'))


class UserAdditionalTest(APITestCase):
    def setUp(self) -> None:
        self.user1 = User.objects.create_user(email='test1@gmail.com', username='test1_username', password='test_1234')
        self.user2 = User.objects.create_user(email='test2@gmail.com', username='test2_username', password='test_1234')
        self.client.login(username='test1@gmail.com', password='test_1234')

    def test_user_additional_create_api(self):
        url = reverse('user_additional')

        user_additional1_data = {
            'user': self.user1.id,
            'gender_interested': 'M',
            'weight': 78,
            'height': 185,
            'birthDate': timezone.datetime(year=2000, month=6, day=25).date(),
            'bustSize': 68,
            'waistSize': 50,
            'hipSize': 72,
            'legLength': 140,
            'shoeSize': 40,
        }
        response = self.client.post(url, data=user_additional1_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            {'id', 'user', 'weight', 'height', 'birthDate', 'bustSize', 'waistSize', 'hipSize',
             'legLength', 'shoeSize', 'genderInterested', 'shirtFits', 'trouserFits'}, set(response.json().keys()))
        self.assertEqual([], response.json().get('shirtFits'))
        self.assertEqual([], response.json().get('trouserFits'))

        user_additional2_data = {
            "user": self.user2.id,
            "weight": 60,
            "height": 170,
            'gender_interested': 'F',
            "birthDate": "1990-01-01",
            "bustSize": 90,
            "waistSize": 75,
            "hipSize": 95,
            "legLength": 75,
            "shoeSize": 42,
            "shirtFits": [
                {"fitType": "Slim"},
            ],
            "trouserFits": [
                {"fitType": "Skinny"},
                {"fitType": "Slim"},
                {"fitType": "Normal"},
                {"fitType": "Loose"},
            ],
        }

        response = self.client.post(url, data=user_additional2_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(len(user_additional2_data.get('shirtFits')), 1)
        self.assertEqual(len(user_additional2_data.get('shirtFits')), len(response.json().get('shirtFits')))
        self.assertEqual({'id', 'userAdditional', 'fitType'}, set(response.json().get('shirtFits')[0].keys()))
        self.assertEqual(len(user_additional2_data.get('trouserFits')), 4)
        self.assertEqual(len(user_additional2_data.get('trouserFits')), len(response.json().get('trouserFits')))
        self.assertEqual({'id', 'userAdditional', 'fitType'}, set(response.json().get('trouserFits')[0].keys()))

        response = self.client.post(url, data=user_additional2_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user', response.json().keys())
        self.assertIn('user additional with this user already exists.', response.json().get('user'))


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

    def request_otp_api(self, user_email):
        url = reverse('request_otp')
        return self.client.post(
            url, data={'email': user_email},
            **{'HTTP_AUTHORIZATION': f'Bearer {self.user_access_token}'}
        )

    def test_request_otp(self):
        response = self.request_otp_api(self.user.email)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.request_otp_api(self.user.email)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_verify_otp(self):
        self.request_otp_api(self.user.email)
        otp_code = OTP.objects.filter(user__email=self.user.email).first().code

        url = reverse('verify_otp')

        """Wrong OTP"""
        response = self.client.post(
            url, data={'email': self.user.email, 'code': '-----'},
            **{'HTTP_AUTHORIZATION': f'Bearer {self.user_access_token}'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('code' in response.json())
        self.assertEqual(response.json().get('code'), ['Code is not valid.'])
        self.assertFalse(User.objects.get(id=self.user.id).is_verified)

        """Correct OTP"""
        response = self.client.post(
            url, data={'email': self.user.email, 'code': otp_code},
            **{'HTTP_AUTHORIZATION': f'Bearer {self.user_access_token}'}
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(User.objects.get(id=self.user.id).is_verified)
