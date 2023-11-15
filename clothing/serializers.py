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
    has_discount = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'title', 'preview_image', 'brand', 'has_discount')


class VariantPreviewSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField(source='product_id')
    has_discount = serializers.BooleanField(read_only=True)

    class Meta:
        model = Variant
        fields = ('id', 'product', 'has_discount', 'image_src', 'link', 'original_price', 'final_price', 'is_available',
                  'color_hex', 'size', 'option1', 'option2')


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


class SavedVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedVariant
        fields = '__all__'


class TrackedVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackedVariant
        fields = '__all__'
