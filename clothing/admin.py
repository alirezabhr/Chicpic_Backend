from django.contrib import admin

# Register your models here.
from clothing.models import Category, Shop, Product, Attribute, ProductAttribute, Variant, SizeGuide, SavedVariant, \
    TrackedVariant

admin.site.register(Category)
admin.site.register(Shop)
admin.site.register(Product)
admin.site.register(Attribute)
admin.site.register(ProductAttribute)
admin.site.register(Variant)
admin.site.register(SizeGuide)
admin.site.register(TrackedVariant)
admin.site.register(SavedVariant)
