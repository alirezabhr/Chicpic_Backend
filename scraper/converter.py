import os
import django
from abc import ABC, abstractmethod

from scraper import utils, constants

# Set up the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chicpic.settings")
django.setup()

from clothing.models import Category, Shop, Product, Variant, Attribute, SizeGuide


class DataConverter(ABC):
    def __init__(self, shop_name: str):
        self._shop_name = shop_name

    @abstractmethod
    def convert_product(self, product: dict, shop: Shop) -> Product:
        pass

    @abstractmethod
    def convert_variant(self, variant: dict, product: Product) -> Variant:
        pass

    @abstractmethod
    def convert_attribute(self, name: str, value: str, variant: Variant) -> Attribute:
        pass

    @abstractmethod
    def convert_size_guide(self, option: str, value: str, variant: Variant) -> SizeGuide:
        pass

    @abstractmethod
    def convert_category(self, category_title: str, category_gender: str) -> Category:
        pass

    @property
    def shop(self) -> Shop:
        try:
            shop = Shop.objects.get(name__iexact=self._shop_name)
        except Shop.DoesNotExist:
            shop = Shop.objects.create(name=self._shop_name)
        return shop


class KitAndAceDataConverter(DataConverter):
    __SHOP_NAME = constants.Shops.KIT_AND_ACE.value
    __BRAND_NAME = constants.Shops.KIT_AND_ACE.value

    def __init__(self):
        super().__init__(self.__SHOP_NAME)

    def convert_product(self, product: dict, shop: Shop) -> Product:
        # TODO check if it has more than 1 gender
        category = self.convert_category(product['category'], product['genders'][0])

        return Product.objects.create(
            shop=shop,
            brand=self.__BRAND_NAME,
            title=product['title'],
            description=product['description'],
            category=category
        )

    def convert_variant(self, variant: dict, product: Product) -> Variant:
        return Variant.objects.create(
            product=product,
            image=variant['image']['src'],
            link=variant['link'],
            original_price=variant['original_price'],
            final_price=variant['final_price'],
            is_available=variant['available']
        )

    def convert_attribute(self, name: str, value: str, variant: Variant) -> Attribute:
        attr_name = utils.find_proper_choice(Attribute.AttributeNameChoices.choices, name)
        return Attribute.objects.create(variant=variant, name=attr_name, value=value)

    def convert_size_guide(self, option: str, value: str, variant: Variant) -> SizeGuide:
        pass
        # TODO implement
        # with open(f'shop_size_guides/{constants.SIZE_GUIDE.format(shop_name=self.__SHOP_NAME, type=)}.csv', 'r') as f:
        #
        # option_choice = utils.find_proper_choice(SizeGuide.SizeGuideOptionChoices.choices, option)
        # SizeGuide.objects.create(variant=variant, option=option_choice, value=value)

    def convert_category(self, category_title: str, category_gender: str) -> Category:
        # Find the equivalent name in clothing.fixtures.categories file

        kit_and_ace_categories = [
            {'gender': 'Women', 'title': 'T-Shirts & Tank Tops', 'equivalent_chicpic_name': 'Tops & Shirts'},
            {'gender': 'Women', 'title': 'Long Sleeve Shirts', 'equivalent_chicpic_name': 'Tops & Shirts'},
            {'gender': 'Women', 'title': 'Dresses & Jumpsuits', 'equivalent_chicpic_name': 'Dresses'},
            {'gender': 'Women', 'title': 'Pants', 'equivalent_chicpic_name': 'Bottoms'},
            {'gender': 'Women', 'title': 'Sweatshirts & Hoodies', 'equivalent_chicpic_name': 'Outerwear'},
            {'gender': 'Women', 'title': 'Sweaters', 'equivalent_chicpic_name': 'Sweaters & Cardigans'},
            {'gender': 'Women', 'title': 'Shirts & Blouses', 'equivalent_chicpic_name': 'Tops & Shirts'},
            {'gender': 'Women', 'title': 'Jackets', 'equivalent_chicpic_name': 'Outerwear'},
            {'gender': 'Women', 'title': 'Shorts & Skirts', 'equivalent_chicpic_name': 'Bottoms'},
            {'gender': 'Men', 'title': 'T-Shirts', 'equivalent_chicpic_name': 'Shirts'},
            {'gender': 'Men', 'title': 'Long Sleeve Shirts', 'equivalent_chicpic_name': 'Shirts'},
            {'gender': 'Men', 'title': 'Pants', 'equivalent_chicpic_name': 'Pants'},
            {'gender': 'Men', 'title': 'Sweatshirts & Hoodies', 'equivalent_chicpic_name': 'Outerwear'},
            {'gender': 'Men', 'title': 'Sweaters', 'equivalent_chicpic_name': 'Sweaters'},
            {'gender': 'Men', 'title': 'Shirts', 'equivalent_chicpic_name': 'Shirts'},
            {'gender': 'Men', 'title': 'Jackets & Blazers', 'equivalent_chicpic_name': 'Outerwear'},
            {'gender': 'Men', 'title': 'Shorts', 'equivalent_chicpic_name': 'Shorts'}
        ]

        selected_category = None
        for category in kit_and_ace_categories:
            if category['gender'] == category_gender and category['title'] == category_title:
                selected_category = category
                break

        return Category.objects.get(title=selected_category['equivalent_chicpic_name'])
