from rest_framework import serializers

from .models import Category, Shop, Product, SavedProduct, TrackedProduct


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    shop = ShopSerializer()

    class Meta:
        model = Product
        fields = '__all__'


class ProductSavedTrackedSerializer(ProductSerializer):
    is_saved = serializers.SerializerMethodField(read_only=True)
    is_tracked = serializers.SerializerMethodField(read_only=True)

    def get_is_saved(self, obj):
        request_user = self.context['request'].user
        if request_user:
            return SavedProduct.objects.filter(user=request_user, product_id=obj.id).exists()
        return False

    def get_is_tracked(self, obj):
        request_user = self.context['request'].user
        if request_user:
            return TrackedProduct.objects.filter(user=request_user, product_id=obj.id).exists()
        return False

    class Meta:
        model = Product
        fields = '__all__'
