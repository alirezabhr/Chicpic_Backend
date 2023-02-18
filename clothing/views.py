from django.db.models import Q
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Category, Product, Shop
from .serializers import CategorySerializer, ProductSerializer, ProductSavedTrackedSerializer, ShopSerializer


class CategoriesView(ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        gender = self.request.query_params.get('gender')
        if gender is not None:
            return Category.objects.filter(gender=self.request.query_params.get('gender'))
        return Category.objects.all()


class CategoryProductsView(ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(category_id=self.kwargs.get('category_id'))


class ShopsView(ListAPIView):
    serializer_class = ShopSerializer
    queryset = Shop.objects.all()


class ShopProductsView(ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(shop_id=self.kwargs.get('shop_id'))


class ProductView(ListAPIView):
    serializer_class = ProductSavedTrackedSerializer
    queryset = Product.objects.all()


class ProductDetailView(RetrieveAPIView):
    serializer_class = ProductSavedTrackedSerializer

    def get_object(self):
        return Product.objects.get(id=self.kwargs.get('product_id'))


class ProductSearch(ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q')
        return Product.objects.filter(
            Q(title__icontains=query) |
            Q(shop__name__icontains=query) |
            Q(brand__icontains=query) |
            Q(description__icontains=query)
        )
