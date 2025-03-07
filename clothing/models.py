from django.db import models
from django.db.models import F

from core.models import SoftDeleteModel
from user.models import User, GenderChoices


class Category(models.Model):
    title = models.CharField(max_length=40)
    gender = models.CharField(max_length=1, choices=GenderChoices.choices)
    image = models.ImageField(upload_to='category_images/')
    priority = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('priority',)

    def __str__(self):
        return f'{self.title} / {self.get_gender_display()}'


def shop_image_upload_path(shop_obj, uploaded_file_name):
    file_format = uploaded_file_name.split('.')[-1]
    file_name_and_format = f'image.{file_format}'
    return f'shops/{shop_obj.name}/{file_name_and_format}'


class Shop(SoftDeleteModel):
    name = models.CharField(max_length=50, unique=True)
    website = models.URLField()
    image = models.ImageField(upload_to=shop_image_upload_path, default='default.png')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('name',)

    @property
    def products(self):
        return Product.objects.with_deleted().filter(shop=self)

    def __str__(self):
        return f'{self.id}: {self.name}'


class Attribute(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name='Attribute Name')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return self.name


class Product(SoftDeleteModel):
    original_id = models.BigIntegerField(unique=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=60)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def variants(self):
        return Variant.objects.filter(product=self)

    @property
    def preview_image(self):
        return Variant.objects.filter(product=self).first().image_src

    @property
    def attributes(self):
        return ProductAttribute.objects.filter(product=self)

    @property
    def has_discount(self):
        return Variant.objects.filter(product=self, final_price__lt=F('original_price')).exists()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('-id',)


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_attributes')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='product_attributes')
    position = models.PositiveSmallIntegerField()

    @property
    def name(self):
        return self.attribute.name

    @property
    def values(self):
        field_name = f'option{self.position}'
        return self.product.variants.values_list(field_name, flat=True).distinct().order_by()

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(position__in=[0, 1, 2]), name='valid_position'),
            models.UniqueConstraint(fields=['product', 'attribute'], name='unique_product_attribute'),
            models.UniqueConstraint(fields=['product', 'position'], condition=models.Q(position__gt=0),
                                    name='unique_product_position'),
        ]
        ordering = ('position',)


def variant_image_upload_path(variant_obj, uploaded_file_name):
    file_format = uploaded_file_name.split('.')[-1]
    file_name_and_format = f'image.{file_format}'
    return f'products/shop_{variant_obj.product.shop.id}/product_{variant_obj.product.id}/{file_name_and_format}'


class Variant(models.Model):
    original_id = models.BigIntegerField(unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    image_src = models.URLField(max_length=300)
    link = models.URLField(max_length=256)
    original_price = models.DecimalField(max_digits=6, decimal_places=2)
    final_price = models.DecimalField(max_digits=6, decimal_places=2)
    is_available = models.BooleanField(verbose_name='Available')
    # color_hex size is 20 because it can be combination of up to 3 colors
    color_hex = models.CharField(max_length=20, null=True, blank=True)
    size = models.CharField(max_length=10, null=True, blank=True)
    option1 = models.CharField(max_length=40, null=True, blank=True)
    option2 = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        ordering = ('-id',)

    @property
    def has_discount(self):
        return self.final_price < self.original_price

    @property
    def discount_rate(self):
        return int((self.original_price - self.final_price) / self.original_price * 100)

    def __str__(self):
        return str(self.id)


class Sizing(models.Model):
    class SizingOptionChoices(models.TextChoices):
        BUST = 'Bust', 'Bust'
        WAIST = 'Waist', 'Waist'
        INSEAM = 'Inseam', 'Inseam'
        HIPS = 'Hips', 'Hips'
        SHOULDER = 'Shoulder', 'Shoulder'
        CHEST = 'Chest', 'Chest'
        HEIGHT = 'Height', 'Height'
        NECK = 'Neck', 'Neck'
        SHOE_SIZE = 'Shoe Size', 'Shoe Size'

    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='sizings')
    option = models.CharField(max_length=20, choices=SizingOptionChoices.choices)
    value = models.DecimalField(max_digits=4, decimal_places=1)

    class Meta:
        unique_together = ('variant', 'option')

    def __str__(self):
        return f'{self.option} - {self.value}'

# TODO: refactor this model
class SavedVariant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'variant')


# TODO: refactor this model
class TrackedVariant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    tracked_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'variant')

    def __str__(self):
        return f'({self.id}) user: {self.user.username} variant: {self.variant.id}'
