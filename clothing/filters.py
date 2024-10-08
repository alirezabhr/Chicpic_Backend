from decimal import Decimal
from django.db.models import Q, F, Case, When, DecimalField, Sum, Window, IntegerField, Count, QuerySet
from django.db.models.functions import Abs, RowNumber, Ceil
from django_filters import rest_framework as rest_filters

from user.models import UserAdditional


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
    ).filter(
        # Ensure that the size difference is within the tolerance range
        Q(sizings__option='Shoulder', sizings__value__range=(shoulder_size - 5, shoulder_size + 5)) |
        (Q(sizings__option='Bust',
           sizings__value__range=(bust_size - 5, bust_size + 5)) if bust_size is not None else Q()) |
        (Q(sizings__option='Chest',
           sizings__value__range=(chest_size - 5, chest_size + 5)) if chest_size is not None else Q()) |
        Q(sizings__option='Waist', sizings__value__range=(waist_size - 5, waist_size + 5)) |
        Q(sizings__option='Hips', sizings__value__range=(hips_size - 5, hips_size + 5)) |
        Q(sizings__option='Inseam', sizings__value__range=(inseam - 7, inseam + 7)) |
        Q(sizings__option='Shoe Size', sizings__value__range=(shoe_size - Decimal(0.5), shoe_size + Decimal(1)))
    ).annotate(
        rn=Window(
            expression=RowNumber(),
            partition_by=[F('product_id')],
            order_by=(F('diff_sum'),)
        )
    ).filter(rn=1)

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


class VariantBaseFilter(rest_filters.FilterSet):
    available = rest_filters.BooleanFilter(field_name='is_available')
    min_price = rest_filters.NumberFilter(field_name='final_price', lookup_expr='gte')
    max_price = rest_filters.NumberFilter(field_name='final_price', lookup_expr='lte')
    recommended = rest_filters.BooleanFilter(method='get_recommended_variants', label="Show Recommended?")

    def get_recommended_variants(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        """
        Filter variants based on recommendation logic.
        If user has body size information, returns best fit variants.
        Otherwise, returns middle-sized variants.
        """

        # Order queryset by random
        queryset = queryset.order_by('?')

        if value:
            user_additional = self.request.user.additional
            return get_best_fit_variant(user_additional, queryset)
        else:
            return get_middle_variants(queryset)


class VariantGenderInterestedFilter(VariantBaseFilter):
    def get_recommended_variants(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        """
        Filter variants based on user interested gender, if value is True.
        """

        if value:
            user_additional = self.request.user.additional
            queryset = queryset.filter(product__categories__gender=user_additional.gender_interested)

        return super().get_recommended_variants(queryset, name, value)


class VariantDiscountFilter(VariantBaseFilter):
    gender = rest_filters.CharFilter(field_name='product__categories__gender')
    discount = rest_filters.NumberFilter(method='filter_discount', label='Discount Rate')

    def filter_discount(self, queryset: QuerySet, name: str, value: Decimal) -> QuerySet:
        """
        Filter variants based on discount rate.
        """

        return queryset.annotate(
            discount=(F('original_price') - F('final_price')) / F('original_price') * 100
        ).filter(
            discount__gte=value
        )