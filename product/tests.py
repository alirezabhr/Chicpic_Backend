from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from django.contrib.auth import get_user_model

from .models import Category

User = get_user_model()


class CategoryTest(APITestCase):
    def setUp(self) -> None:
        User.objects.create_user(email='user@chicpic.app', username='user_user', password='test1234')
        self.client.login(username='user_user', password='test1234')

    def test_object_creation(self):
        category1_data = {'title': 'shirt', 'gender': 'F'}
        category2_data = {'title': 'pants', 'gender': 'M'}
        Category.objects.create(**category1_data)
        Category.objects.create(**category2_data)

        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(Category.objects.all().first().title, category1_data.get('title'))
        self.assertEqual(Category.objects.all()[1].gender, category2_data.get('gender'))

    def test_get_categories_list(self):
        # Create categories
        Category.objects.bulk_create([
            Category(title='New In', gender=Category.GenderChoices.FEMALE),
            Category(title='Clothing', gender=Category.GenderChoices.FEMALE),
            Category(title='Dresses', gender=Category.GenderChoices.FEMALE),
            Category(title='Shoes', gender=Category.GenderChoices.FEMALE),
            Category(title='Pants', gender=Category.GenderChoices.MALE),
            Category(title='Shoes', gender=Category.GenderChoices.MALE),
        ])

        # ALL Categories
        url = reverse('get_categories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), Category.objects.count())

        # Men's Categories
        url = reverse('get_categories') + '?gender=M'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), Category.objects.filter(gender=Category.GenderChoices.MALE).count())

        # Women's Categories
        url = reverse('get_categories') + '?gender=F'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), Category.objects.filter(gender=Category.GenderChoices.FEMALE).count())
