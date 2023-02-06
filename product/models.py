from django.db import models

from user.models import User


class Category(models.Model):
    class GenderChoices(models.TextChoices):
        FEMALE = 'F', 'Female'
        MALE = 'M', 'Male'

    title = models.CharField(max_length=40)
    gender = models.CharField(max_length=1, choices=GenderChoices.choices)


class Brand(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


def product_image_upload_path(product_obj, uploaded_file_name):
    file_format = uploaded_file_name.split('.')[-1]
    file_name_and_format = f'image.{file_format}'
    return f'products/{product_obj.brand.name}/{product_obj.title}/{file_name_and_format}'


class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=350, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    image = models.ImageField(upload_to=product_image_upload_path)
    link = models.URLField(max_length=256)
    original_price = models.DecimalField(max_digits=5, decimal_places=2)
    final_price = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    is_deleted = models.BooleanField(default=False)
