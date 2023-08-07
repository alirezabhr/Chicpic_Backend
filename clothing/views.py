from django.db.models import Q, F, Case, When, DecimalField, Sum, Window, IntegerField, Count
from django.db.models.functions import Abs, RowNumber, Ceil
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from user.models import UserAdditional
from .models import Category, Product, Shop, Variant, TrackedVariant
from .serializers import CategorySerializer, ShopSerializer, ProductPreviewSerializer, \
    VariantPreviewSerializer, ProductDetailSerializer, TrackedVariantSerializer


class CategoriesView(ListAPIView):
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        gender = self.request.query_params.get('gender')
        if gender is not None:
            return Category.objects.filter(gender=self.request.query_params.get('gender'))
        return Category.objects.all()


class CategoryProductsView(ListAPIView):
    serializer_class = ProductPreviewSerializer

    def get_queryset(self):
        category = get_object_or_404(Category, id=self.kwargs.get('category_id'))
        return category.products.all()


class ShopsView(ListAPIView):
    serializer_class = ShopSerializer
    queryset = Shop.objects.all()


class ShopProductsView(ListAPIView):
    serializer_class = ProductPreviewSerializer

    def get_queryset(self):
        return Product.objects.filter(shop_id=self.kwargs.get('shop_id'))


class VariantsView(ListAPIView):
    serializer_class = VariantPreviewSerializer
    queryset = Variant.objects.all()


class ExploreVariantsView(ListAPIView):
    serializer_class = VariantPreviewSerializer

    def get_queryset(self):
        user = self.request.user

        try:
            user_additional = user.additional
        except UserAdditional.DoesNotExist:
            user_additional = None

        if user_additional is not None:  # find the best fit clothes if user additional exists
            # TODO: handle One Size Fit All (OSFA) products
            gender_interested = user_additional.gender_interested
            shoulder_size = user_additional.shoulder_size
            bust_size = user_additional.bust_size
            chest_size = user_additional.chest_size
            waist_size = user_additional.waist_size
            hips_size = user_additional.hips_size
            inseam = user_additional.inseam
            shoe_size = user_additional.shoe_size

            # Filter variants based on gender and categories
            queryset = Variant.objects.filter(
                product__categories__gender=gender_interested
            ).annotate(
                diff_sum=Sum(
                    Case(
                        When(sizings__option='Shoulder', then=Abs(F('sizings__value') - shoulder_size)),
                        When(sizings__option='Bust', then=Abs(F('sizings__value') - bust_size)),
                        When(sizings__option='Chest', then=Abs(F('sizings__value') - chest_size)),
                        When(sizings__option='Waist', then=Abs(F('sizings__value') - waist_size)),
                        When(sizings__option='Hips', then=Abs(F('sizings__value') - hips_size)),
                        When(sizings__option='Inseam', then=Abs(F('sizings__value') - inseam)),
                        When(sizings__option='Shoe Size', then=Abs(F('sizings__value') - shoe_size)),
                        output_field=DecimalField(max_digits=4, decimal_places=1)
                    )
                )
            ).annotate(
                rn=Window(
                    expression=RowNumber(),
                    partition_by=[F('product_id')],
                    order_by=(F('diff_sum'),)
                )
            ).filter(rn=1, is_available=True).order_by('-product_id', 'id').values(
                'id', 'image_src', 'link', 'original_price', 'final_price', 'is_available', 'color_hex', 'option1',
                'option2', 'product_id',
            )
        else:
            queryset = Variant.objects.filter(
                is_available=True
            ).annotate(
                row_number=Window(
                    expression=RowNumber(),
                    partition_by=[F('product_id')],
                    order_by=(F('id'),)
                ),
                num_variants=Count('product__variants', distinct=True, output_field=IntegerField())
            ).annotate(
                middle_variant_id=Case(
                    When(row_number=Ceil(F('num_variants') / 2), then=F('id')),
                    default=None,
                    output_field=IntegerField()
                )
            ).filter(
                middle_variant_id=F('id')
            ).order_by('-product_id')

        return queryset


class ProductDetailView(RetrieveAPIView):
    serializer_class = ProductDetailSerializer

    def get_object(self):
        return Product.objects.get(id=self.kwargs.get('product_id'))


class ProductSearch(ListAPIView):
    serializer_class = ProductPreviewSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q')
        return Product.objects.filter(
            Q(title__icontains=query) |
            Q(shop__name__icontains=query) |
            Q(brand__icontains=query) |
            Q(description__icontains=query)
        )


class TrackVariantView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        user = data.get('user')
        variant = data.get('variant')

        tracked_variant = TrackedVariant.objects.filter(user=user, variant=variant).first()

        if tracked_variant:
            serializer = TrackedVariantSerializer(tracked_variant, data=data)
        else:
            serializer = TrackedVariantSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)