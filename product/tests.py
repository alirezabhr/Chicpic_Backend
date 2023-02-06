from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status

from django.contrib.auth import get_user_model

from .models import Category, Brand, Product

User = get_user_model()


def create_categories():
    Category.objects.bulk_create([
        Category(title='New In', gender=Category.GenderChoices.FEMALE),
        Category(title='Clothing', gender=Category.GenderChoices.FEMALE),
        Category(title='Dresses', gender=Category.GenderChoices.FEMALE),
        Category(title='Shoes', gender=Category.GenderChoices.FEMALE),
        Category(title='Pants', gender=Category.GenderChoices.MALE),
        Category(title='Shoes', gender=Category.GenderChoices.MALE),
    ])
    return Category.objects.all()


def create_brands():
    Brand.objects.bulk_create([
        Brand(name='Nike'),
        Brand(name='Gap'),
        Brand(name='H&M'),
    ])
    return Brand.objects.all()


def create_products(product_image):
    Product.objects.bulk_create([
        Product(
            brand=Brand.objects.get(name='Nike'),
            title='Nike Sportswear Swoosh',
            description="Women's Woven Jacket",
            category=Category.objects.get(title='Clothing'),
            image=product_image,
            link='https://chicpic.app/',
            original_price=120,
        ),
        Product(
            brand=Brand.objects.get(name='Nike'),
            title='Nike Zenvy',
            description="Women's Gentle-Support High-Waisted 7/8 Leggings",
            category=Category.objects.get(title='Clothing'),
            image=product_image,
            link='https://chicpic.app/',
            original_price=70,
        ),
        Product(
            brand=Brand.objects.get(name='Gap'),
            title='Twill Shirt',
            description='',
            category=Category.objects.get(title='Dresses'),
            image=product_image,
            link='https://chicpic.app/',
            original_price=59.95,
            final_price=35,
        ),
    ])
    return Product.objects.all()


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
        create_categories()

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


class ProductTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(email='user@chicpic.app', username='user_user', password='test1234')
        self.client.login(username='user_user', password='test1234')

        # Create categories
        create_categories()

        # Create brands
        create_brands()

        self.product_image = SimpleUploadedFile(
            name='product_image.jpg',
            content=open('media/test/product_image.jpg', 'rb').read(),
            content_type='image/jpeg',
        )

        products = create_products(self.product_image)
        self.product1 = products[0]
        self.product2 = products[1]
        self.product3 = products[2]

    def test_get_category_products(self):
        category_id = Category.objects.get(title='Clothing').id
        url = reverse('category_products', kwargs={'category_id': category_id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), Product.objects.filter(category_id=category_id).count())
        self.assertEqual(response.json()[0].get('category'), category_id)
