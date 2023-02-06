from rest_framework import serializers

from .models import Category, Brand, Product, SavedProduct, TrackedProduct


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ProductDetailSerializer(serializers.ModelSerializer):
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
