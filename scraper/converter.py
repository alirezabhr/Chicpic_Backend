import json
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

    @utils.log_function_call
    @abstractmethod
    def convert_product(self, product: dict, shop: Shop) -> Product:
        pass

    @utils.log_function_call
    @abstractmethod
    def convert_variant(self, variant: dict, product: Product) -> Variant:
        pass

    @utils.log_function_call
    @abstractmethod
    def convert_attribute(self, name: str, value: str, variant: Variant) -> Attribute:
        pass

    @utils.log_function_call
    @abstractmethod
    def convert_size_guide(self, size_guide_type: str, size_value: str, variant: Variant) -> SizeGuide:
        pass

    @utils.log_function_call
    def convert_category(self, category_title: str, category_gender: str) -> Category:
        # Load shop categories file
        with open(constants.SHOP_CATEGORIES_FILE_PATH.format(shop_name=self._shop_name), 'r') as f:
            kit_and_ace_categories = json.loads(f.read())

        # Find proper chicpic category similar according to shop categories
        selected_category = None
        for category in kit_and_ace_categories:
            if category['gender'] == category_gender and category['title'] == category_title:
                selected_category = category
                break
        else:
            # TODO log error
            print(f'category_title: {category_title}, category_gender: {category_gender}')

        if selected_category is not None:
            gender = utils.find_proper_choice(Category.GenderChoices.choices, selected_category['gender'])
            return Category.objects.get(title=selected_category['equivalent_chicpic_name'], gender=gender)

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
            image_src=variant['image']['src'],
            link=variant['link'],
            original_price=variant['original_price'],
            final_price=variant['final_price'],
            is_available=variant['available']
        )

    def convert_attribute(self, name: str, value: str, variant: Variant) -> Attribute:
        attr_name = utils.find_proper_choice(Attribute.AttributeNameChoices.choices, name)
        return Attribute.objects.create(variant=variant, name=attr_name, value=value)

    def convert_size_guide(self, size_guide_type: str, size_value: str, variant: Variant) -> SizeGuide:
        # TODO implement
        pass
        # file_path = constants.SHOP_SIZE_GUIDES_FILE_PATH.format(shop_name=self._shop_name, size_guide_type=size_guide_type)
        # with open(file_path, 'r') as f:
        #     pass
        # option_choice = utils.find_proper_choice(SizeGuide.SizeGuideOptionChoices.choices, option)
        # SizeGuide.objects.create(variant=variant, option=option_choice, value=value)
