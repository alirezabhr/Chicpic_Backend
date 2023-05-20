from rest_framework import serializers

from .models import Category, Shop, Attribute, Product, ProductAttribute, Variant, SavedVariant, TrackedVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'


class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = '__all__'


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ('id', 'position', 'name', 'values')


class ProductPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'title', 'preview_image', 'brand')


class VariantPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = '__all__'


class VariantDetailSerializer(serializers.ModelSerializer):
    is_saved = serializers.SerializerMethodField(read_only=True)
    is_tracked = serializers.SerializerMethodField(read_only=True)

    def get_is_saved(self, obj):
        request_user = self.context['request'].user
        if request_user:
            return SavedVariant.objects.filter(user=request_user, variant_id=obj.id).exists()
        return False

    def get_is_tracked(self, obj):
        request_user = self.context['request'].user
        if request_user:
            return TrackedVariant.objects.filter(user=request_user, variant_id=obj.id).exists()
        return False

    class Meta:
        model = Variant
        fields = '__all__'


class ProductDetailSerializer(serializers.ModelSerializer):
    preview_image = serializers.ReadOnlyField()
    shop = ShopSerializer()
    variants = VariantDetailSerializer(many=True)
    attributes = ProductAttributeSerializer(many=True)

    class Meta:
        model = Product
        fields = '__all__'
