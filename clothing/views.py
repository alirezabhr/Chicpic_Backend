from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .filters import VariantBaseFilter, VariantGenderInterestedFilter, VariantDiscountFilter
from .models import Category, Product, Shop, Variant, TrackedVariant, SavedVariant
from .serializers import CategorySerializer, ShopSerializer, ProductPreviewSerializer, \
    VariantPreviewSerializer, ProductDetailSerializer, SavedVariantSerializer, TrackedVariantSerializer


class CategoriesView(ListAPIView):
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        gender = self.request.query_params.get('gender')
        if gender is not None:
            # Categories with the gender specified and which has products
            return Category.objects.filter(gender=gender, products__isnull=False).distinct()
        else:
            return Category.objects.all()


class CategoryProductsView(ListAPIView):
    serializer_class = ProductPreviewSerializer

    def get_queryset(self):
        category = get_object_or_404(Category, id=self.kwargs.get('category_id'))
        return category.products.all()


class CategoryVariantsView(ListAPIView):
    serializer_class = VariantPreviewSerializer
    filterset_class = VariantBaseFilter

    def get_queryset(self):
        category_variants = Variant.objects.filter(product__categories__id=self.kwargs.get('category_id'))
        return category_variants


class DiscountedCategoryVariantsView(ListAPIView):
    serializer_class = VariantPreviewSerializer
    queryset = Variant.objects.all()
    filterset_class = VariantDiscountFilter


class ShopsView(ListAPIView):
    serializer_class = ShopSerializer
    queryset = Shop.objects.all()


class ShopProductsView(ListAPIView):
    serializer_class = ProductPreviewSerializer

    def get_queryset(self):
        return Product.objects.filter(shop_id=self.kwargs.get('shop_id'))


class ShopVariantsView(ListAPIView):
    serializer_class = VariantPreviewSerializer
    filterset_class = VariantGenderInterestedFilter

    def get_queryset(self):
        shop_variants = Variant.objects.filter(product__shop_id=self.kwargs.get('shop_id'))
        return shop_variants


class ExploreVariantsView(ListAPIView):
    serializer_class = VariantPreviewSerializer
    queryset = Variant.objects.all()
    filterset_class = VariantGenderInterestedFilter


class ProductsView(ListAPIView):
    serializer_class = ProductPreviewSerializer
    queryset = Product.objects.with_deleted()


class ProductDetailView(RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    queryset = Product.objects.with_deleted()
    lookup_field = 'id'
    lookup_url_kwarg = 'product_id'


class VariantSearchView(ListAPIView):
    serializer_class = VariantPreviewSerializer
    queryset = Variant.objects.all()
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = VariantBaseFilter
    search_fields = ('product__title', 'product__description', 'product__shop__name', 'product__brand')


# TODO: refactor this view
class SaveVariantView(APIView):
    serializer = SavedVariantSerializer

    def get_object(self):
        return SavedVariant.objects.filter(user_id=self.request.data.get('user'),
                                           variant_id=self.request.data.get('variant')).first()

    def post(self, request, *args, **kwargs):
        saved_variant = self.get_object()

        if saved_variant is None:
            serializer = self.serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            saved_variant.is_deleted = False
            saved_variant.save()
            return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        saved_variant = self.get_object()
        saved_variant.is_deleted = True
        saved_variant.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


# TODO: refactor this view
class TrackVariantView(APIView):
    serializer = TrackedVariantSerializer

    def get_object(self):
        return TrackedVariant.objects.filter(user_id=self.request.data.get('user'),
                                             variant_id=self.request.data.get('variant')).first()

    def post(self, request, *args, **kwargs):
        tracked_variant = self.get_object()

        if tracked_variant is None:
            serializer = self.serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            tracked_variant.is_deleted = False
            tracked_variant.save()
            return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        tracked_variant = self.get_object()
        tracked_variant.is_deleted = True
        tracked_variant.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class SavedVariantsView(ListAPIView):
    serializer_class = VariantPreviewSerializer

    def get_queryset(self):
        return Variant.objects.filter(savedvariant__user_id=self.kwargs.get('user_id'), savedvariant__is_deleted=False)
