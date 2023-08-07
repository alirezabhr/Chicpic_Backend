from django.contrib import admin

# Register your models here.
from clothing.models import Category, Shop, Product, Attribute, ProductAttribute, Variant, Sizing, SavedVariant, \
    TrackedVariant

class TrackedVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'variant', 'tracked_at')

admin.site.register(Category)
admin.site.register(Shop)
admin.site.register(Product)
admin.site.register(Attribute)
admin.site.register(ProductAttribute)
admin.site.register(Variant)
admin.site.register(Sizing)
admin.site.register(TrackedVariant, TrackedVariantAdmin)
admin.site.register(SavedVariant)
