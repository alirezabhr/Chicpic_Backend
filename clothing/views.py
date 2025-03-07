from django.db.models import Q, F, Case, When, DecimalField, Sum, Window, IntegerField, Count
from django.db.models.functions import Abs, RowNumber, Ceil
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from user.models import UserAdditional
from .models import Category, Product, Shop, Variant, TrackedVariant, SavedVariant
from .serializers import CategorySerializer, ShopSerializer, ProductPreviewSerializer, \
    VariantPreviewSerializer, ProductDetailSerializer, SavedVariantSerializer, TrackedVariantSerializer


def get_best_fit_variant(user_additional: UserAdditional, sorted_variants_queryset):
    # TODO: handle One Size Fit All (OSFA) products
    shoulder_size = user_additional.shoulder_size
    bust_size = user_additional.bust_size
    chest_size = user_additional.chest_size
    waist_size = user_additional.waist_size
    hips_size = user_additional.hips_size
    inseam = user_additional.inseam
    shoe_size = user_additional.shoe_size

    # Filter variants based on gender and categories
    queryset = sorted_variants_queryset.filter(
        product__is_deleted=False
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
    ).filter(rn=1, is_available=True)

    return queryset


def get_middle_variants(sorted_variants_queryset):
    queryset = sorted_variants_queryset.filter(
        product__is_deleted=False,
        is_available=True
    ).annotate(
        row_number=Window(
            expression=RowNumber(output_field=IntegerField()),
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
    )

    return queryset


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

    def get_queryset(self):
        category_variants = Variant.objects.filter(product__categories__id=self.kwargs.get('category_id'),
                                                   product__is_deleted=False)

        # Get the boolean value of a query parameter
        show_recommendations_qp = self.request.query_params.get('recom')
        show_recommendations = show_recommendations_qp is not None and show_recommendations_qp.lower() in ('true', '1')

        try:
            user_additional = self.request.user.additional
        except UserAdditional.DoesNotExist:
            user_additional = None

        if show_recommendations and user_additional is not None:  # find the best fit clothes in that category if user additional exists
            queryset = get_best_fit_variant(user_additional, category_variants)
        else:
            queryset = get_middle_variants(category_variants)

        return queryset


class ShopsView(ListAPIView):
    serializer_class = ShopSerializer
    queryset = Shop.objects.all()


class ShopProductsView(ListAPIView):
    serializer_class = ProductPreviewSerializer

    def get_queryset(self):
        return Product.objects.filter(shop_id=self.kwargs.get('shop_id'))


class ShopVariantsView(ListAPIView):
    serializer_class = VariantPreviewSerializer

    def get_queryset(self):
        user = self.request.user

        # Get the boolean value of a query parameter
        show_recommendations_qp = self.request.query_params.get('recom')
        show_recommendations = show_recommendations_qp is not None and show_recommendations_qp.lower() in ('true', '1')

        try:
            user_additional = user.additional
        except UserAdditional.DoesNotExist:
            user_additional = None

        # Variants in random order
        queryset = Variant.objects.filter(product__shop_id=self.kwargs.get('shop_id'))

        if show_recommendations and user_additional is not None:  # find the best fit clothes if user additional exists
            queryset = queryset.filter(product__categories__gender=user_additional.gender_interested)
            queryset = get_best_fit_variant(user_additional, queryset)
        else:
            queryset = get_middle_variants(queryset)

        return queryset



class VariantsView(ListAPIView):
    serializer_class = VariantPreviewSerializer

    def filter_gender(self, queryset):
        gender = self.request.query_params.get('gender')
        if gender is not None:
            queryset = queryset.filter(product__categories__gender=gender)
        return queryset

    def filter_discount(self, queryset):
        discount = self.request.query_params.get('discount')
        if discount is not None:
            queryset = queryset.filter(product__is_deleted=False).annotate(
                discount=(F('original_price') - F('final_price')) / F('original_price') * 100).filter(
                discount__gte=discount).distinct()
        else:
            queryset = queryset.filter(product__is_deleted=False)
        return queryset

    def get_queryset(self):
        variants_queryset = self.filter_discount(self.filter_gender(Variant.objects.all()))

        # Get the boolean value of a query parameter
        show_recommendations_qp = self.request.query_params.get('recom')
        show_recommendations = show_recommendations_qp is not None and show_recommendations_qp.lower() in ('true', '1')

        try:
            user_additional = self.request.user.additional
        except UserAdditional.DoesNotExist:
            user_additional = None

        if show_recommendations and user_additional is not None:  # find the best fit clothes in that category if user additional exists
            queryset = get_best_fit_variant(user_additional, variants_queryset)
        else:
            queryset = get_middle_variants(variants_queryset)

        return queryset


class ExploreVariantsView(ListAPIView):
    serializer_class = VariantPreviewSerializer

    def get_queryset(self):
        user = self.request.user

        # Get the boolean value of a query parameter
        show_recommendations_qp = self.request.query_params.get('recom')
        show_recommendations = show_recommendations_qp is not None and show_recommendations_qp.lower() in ('true', '1')

        try:
            user_additional = user.additional
        except UserAdditional.DoesNotExist:
            user_additional = None

        # Variants in random order
        queryset = Variant.objects.all().order_by('?')

        if show_recommendations and user_additional is not None:  # find the best fit clothes if user additional exists
            queryset = queryset.filter(product__categories__gender=user_additional.gender_interested)
            queryset = get_best_fit_variant(user_additional, queryset)
        else:
            queryset = get_middle_variants(queryset)

        return queryset


class ProductsView(ListAPIView):
    serializer_class = ProductPreviewSerializer

    def get_queryset(self):
        discount = self.request.query_params.get('discount')
        if discount is not None:
            return Product.objects.annotate(
                discount=(F('variants__original_price') - F('variants__final_price')) / F(
                    'variants__original_price') * 100).filter(discount__gte=discount).distinct()
        return Product.objects.all()


class ProductDetailView(RetrieveAPIView):
    serializer_class = ProductDetailSerializer

    def get_object(self):
        return Product.objects.with_deleted().get(id=self.kwargs.get('product_id'))


class VariantSearchView(ListAPIView):
    serializer_class = VariantPreviewSerializer

    def get_queryset(self):
        query_param = self.request.query_params.get('q')

        queryset = Variant.objects.filter(product__is_deleted=False).filter(
            Q(product__title__icontains=query_param) |
            Q(product__shop__name__icontains=query_param) |
            Q(product__brand__icontains=query_param) |
            Q(product__description__icontains=query_param)
        )

        user = self.request.user

        # Get the boolean value of a query parameter
        show_recommendations_qp = self.request.query_params.get('recom')
        show_recommendations = show_recommendations_qp is not None and show_recommendations_qp.lower() in ('true', '1')

        try:
            user_additional = user.additional
        except UserAdditional.DoesNotExist:
            user_additional = None

        if show_recommendations and user_additional is not None:  # find the best fit clothes if user additional exists
            queryset = get_best_fit_variant(user_additional, queryset)
        else:
            queryset = get_middle_variants(queryset)

        return queryset


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
