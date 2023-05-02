from django.db import models

from user.models import User


class Category(models.Model):
    class Meta:
        verbose_name_plural = 'Categories'

    class GenderChoices(models.TextChoices):
        WOMEN = 'W', 'Women'
        MEN = 'M', 'Men'

    title = models.CharField(max_length=40)
    gender = models.CharField(max_length=1, choices=GenderChoices.choices)
    image = models.ImageField(upload_to='category_images/')

    def __str__(self):
        return f'{self.title} / {self.get_gender_display()}'


def shop_image_upload_path(shop_obj, uploaded_file_name):
    file_format = uploaded_file_name.split('.')[-1]
    file_name_and_format = f'image.{file_format}'
    return f'shops/{shop_obj.name}/{file_name_and_format}'


class Shop(models.Model):
    name = models.CharField(max_length=50, unique=True)
    website = models.URLField()
    image = models.ImageField(upload_to=shop_image_upload_path, default='default.png')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Attribute(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name='Attribute Name')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-id',)


class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=30)
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
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
            models.CheckConstraint(check=models.Q(position__in=[0, 1, 2, 3]), name='valid_position'),
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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    image_src = models.URLField(max_length=300)
    link = models.URLField(max_length=256)
    original_price = models.DecimalField(max_digits=5, decimal_places=2)
    final_price = models.DecimalField(max_digits=5, decimal_places=2)
    is_available = models.BooleanField(verbose_name='Available')
    option1 = models.CharField(max_length=40, null=True, blank=True)
    option2 = models.CharField(max_length=40, null=True, blank=True)
    option3 = models.CharField(max_length=40, null=True, blank=True)

    @property
    def size_guides(self):
        return SizeGuide.objects.filter(variant=self)

    def __str__(self):
        return f'{self.id}: {self.product.shop.name} - {self.product.title}'

    class Meta:
        ordering = ('-id',)


class SizeGuide(models.Model):
    class SizeGuideOptionChoices(models.TextChoices):
        BUST = 'Bust', 'Bust'
        WAIST = 'Waist', 'Waist'
        INSEAM = 'Inseam', 'Inseam'
        HIPS = 'Hips', 'Hips'
        SHOULDER = 'Shoulder', 'Shoulder'
        CHEST = 'Chest', 'Chest'
        HEIGHT = 'Height', 'Height'

    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='size_guides')
    option = models.CharField(max_length=20, choices=SizeGuideOptionChoices.choices)
    value = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('variant', 'option')

    def __str__(self):
        return f'{self.option} - {self.value}'


class SavedVariant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'variant')


class TrackedVariant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    tracked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'variant')
