from rest_framework.generics import ListAPIView

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


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
