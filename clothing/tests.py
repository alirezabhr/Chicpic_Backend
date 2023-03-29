from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status

from django.contrib.auth import get_user_model

from .models import Category, Shop, Product, SavedProduct, TrackedProduct

User = get_user_model()


def create_categories():
    category_image = SimpleUploadedFile(
            name='category_image.png',
            content=open('media/category_images/default.png', 'rb').read(),
            content_type='image/png',
        )

    Category.objects.bulk_create([
        Category(title='New In', gender=Category.GenderChoices.WOMEN, image=category_image),
        Category(title='Clothing', gender=Category.GenderChoices.WOMEN, image=category_image),
        Category(title='Dresses', gender=Category.GenderChoices.WOMEN, image=category_image),
        Category(title='Shoes', gender=Category.GenderChoices.WOMEN, image=category_image),
        Category(title='Pants', gender=Category.GenderChoices.MEN, image=category_image),
        Category(title='Shoes', gender=Category.GenderChoices.MEN, image=category_image),
    ])
    return Category.objects.all()


def create_shops():
    Shop.objects.bulk_create([
        Shop(name='Nike'),
        Shop(name='Gap'),
        Shop(name='H&M'),
    ])
    return Shop.objects.all()


def create_products(product_image):
    Product.objects.bulk_create([
        Product(
            shop=Shop.objects.get(name='Nike'),
            title='Nike Sportswear Swoosh',
            description="Women's Woven Jacket",
            category=Category.objects.get(title='Clothing'),
            image=product_image,
            link='https://chicpic.app/',
            original_price=120,
        ),
        Product(
            shop=Shop.objects.get(name='Nike'),
            title='Nike Zenvy',
            description="Women's Gentle-Support High-Waisted 7/8 Leggings",
            category=Category.objects.get(title='Clothing'),
            image=product_image,
            link='https://chicpic.app/',
            original_price=70,
        ),
        Product(
            shop=Shop.objects.get(name='Gap'),
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
    fixtures = ['categories.json']

    def setUp(self) -> None:
        User.objects.create_user(email='user@chicpic.app', username='user_user', password='test1234')
        self.client.login(username='user_user', password='test1234')

    def test_object_creation(self):
        category1_data = {'title': 'shirt', 'gender': 'W'}
        category2_data = {'title': 'pants', 'gender': 'M'}
        Category.objects.create(**category1_data)
        Category.objects.create(**category2_data)

        self.assertEqual(Category.objects.count(), 17)  # 15 categories in fixture and 2 created

    def test_get_categories_list(self):
        # ALL Categories
        url = reverse('categories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), Category.objects.count())

        # Men's Categories
        url = reverse('categories') + '?gender=M'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), Category.objects.filter(gender=Category.GenderChoices.MEN).count())

        # Women's Categories
        url = reverse('categories') + '?gender=W'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), Category.objects.filter(gender=Category.GenderChoices.WOMEN).count())


class ShopTest(APITestCase):
    def test_shop_creation(self):
        shop_image = SimpleUploadedFile(
            name='shop_image.jpg',
            content=open('media/default.png', 'rb').read(),
            content_type='image/png',
        )
        shop1_data = {'name': 'Shop one', 'image': shop_image}
        shop2_data = {'name': 'Shop two'}

        Shop.objects.create(**shop1_data)
        Shop.objects.create(**shop2_data)

        shops = Shop.objects.all().order_by('created_at')

        self.assertEqual(shops.count(), 2)
        self.assertEqual(shops[0].name, shop1_data.get('name'))


class ProductTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(email='user@chicpic.app', username='user_user', password='test1234')
        self.client.login(username='user_user', password='test1234')

        # Create categories
        create_categories()

        # Create shops
        create_shops()

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

    def test_get_product_detail(self):
        SavedProduct.objects.create(user=self.user, product=self.product1)
        TrackedProduct.objects.create(user=self.user, product=self.product1)
        TrackedProduct.objects.create(user=self.user, product=self.product2)

        for product, is_saved, is_tracked in [
            (self.product1, True, True),
            (self.product2, False, True),
            (self.product3, False, False)
        ]:
            url = reverse('product_detail', kwargs={'product_id': product.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json().get('isSaved'), is_saved)
            self.assertEqual(response.json().get('isTracked'), is_tracked)

    def test_search_products(self):
        url = reverse('search_product') + '?q=NiKe'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

        url = reverse('search_product') + '?q=shirt'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
