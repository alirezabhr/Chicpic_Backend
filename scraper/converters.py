import json
import logging
import os
import csv
import django
from abc import ABC, abstractmethod

from scraper import utils, constants

# Set up the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chicpic.settings")
django.setup()

from clothing.models import Category, Shop, Attribute, Product, ProductAttribute, Variant, Sizing


class DataConverter(ABC):
    def __init__(self, shop: constants.ShopConstant):
        self.shop_name: str = shop.name
        self.shop_website: str = shop.website
        self.__config_logger()

    def __config_logger(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        log_file_formatter = logging.Formatter(
            fmt=f"%(levelname)s %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Create log file if does not exit
        if not os.path.isdir(constants.LOGS_DIR):
            os.makedirs(constants.LOGS_DIR)

        log_file_path = constants.LOGS_FILE_PATH.format(module_name='converters.log')

        if not os.path.exists(log_file_path):
            open(log_file_path, "w").close()

        # Add a file handler to the logger
        file_handler = logging.FileHandler(filename=log_file_path)
        file_handler.setFormatter(log_file_formatter)
        file_handler.setLevel(level=logging.INFO)
        self.logger.addHandler(file_handler)

    def convert_attribute(self, attribute_name: str) -> Attribute:
        try:
            attribute_obj = Attribute.objects.get(name__iexact=attribute_name)
        except Attribute.DoesNotExist:
            attribute_obj = Attribute(name=attribute_name.capitalize())
        return attribute_obj

    @abstractmethod
    def convert_product(self, product: dict, shop: Shop) -> Product:
        pass

    def convert_product_attribute(self, product: Product, attribute: Attribute, position: int) -> ProductAttribute:
        return ProductAttribute(product=product, attribute=attribute, position=position)

    @utils.log_function_call
    @abstractmethod
    def convert_variant(self, variant: dict, product: Product) -> Variant:
        pass

    @utils.log_function_call
    def convert_categories(self, product: dict) -> list[Category]:
        return [self.convert_category(cat, gen) for cat in product['categories'] for gen in product['genders']]

    @utils.log_function_call
    def get_size_guide(self, sizing_type: str) -> csv.DictReader:
        file_path = constants.SHOP_SIZE_GUIDES_FILE_PATH.format(shop_name=self.shop_name, size_guide_type=sizing_type)
        with open(file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
        return reader

    @utils.log_function_call
    def _find_variant_size_value(self, product: dict, variant_id: int):
        selected_variant = list(filter(lambda v: v['id'] == variant_id, product['variants']))[0]

        size_value = None
        for attr in product['attributes']:
            if attr['name'] == 'Size':
                size_value = selected_variant[f"option{attr['position']}"]
                break

        return size_value

    @abstractmethod
    def convert_size_guide(self, product: dict, variant: Variant) -> list[Sizing]:
        pass

    @utils.log_function_call
    def convert_category(self, category_title: str, category_gender: str) -> Category:
        # Load shop categories file
        with open(constants.SHOP_CATEGORIES_CONVERTER_FILE_PATH.format(shop_name=self.shop_name), 'r') as f:
            shop_categories_mapping = json.loads(f.read())

        # Find proper chicpic category similar according to shop categories
        selected_category = None
        for category in shop_categories_mapping:
            if category['gender'] == category_gender and category['title'] == category_title:
                selected_category = category
                break

        if selected_category is None:
            self.logger.error(f'Proper category not found. title: {category_title}, gender: {category_gender}.')
        else:
            gender = utils.find_proper_choice(Category.GenderChoices.choices, selected_category['gender'])
            return Category.objects.get(title=selected_category['equivalent_chicpic_name'], gender=gender)

    @property
    def shop(self) -> Shop:
        try:
            shop_obj = Shop.objects.get(name__iexact=self.shop_name)
        except Shop.DoesNotExist:
            shop_obj = Shop(name=self.shop_name, website=self.shop_website)
        return shop_obj


class KitAndAceDataConverter(DataConverter):
    def __init__(self):
        super().__init__(shop=constants.Shops.KIT_AND_ACE.value)

    @utils.log_function_call
    def convert_product(self, product: dict, shop: Shop) -> Product:
        return Product(
            shop=shop,
            brand=product['brand'],
            title=product['title'],
            description=product['description']
        )

    def __convert_color(self, color_name: str) -> str:
        file_path = constants.COLORS_CONVERTER_FILE_PATH.format(shop_name=self.shop_name)
        with open(file_path, 'r') as f:
            colors_data = json.loads(f.read())
        return colors_data.get(color_name)

    def convert_variant(self, variant: dict, product: Product) -> Variant:
        return Variant(
            product=product,
            image_src=variant['image']['src'],
            link=variant['link'],
            original_price=variant['original_price'],
            final_price=variant['final_price'],
            is_available=variant['available'],
            option1=variant['option1'],
            option2=variant['option2'],
            color=self.__convert_color(variant['color']),
        )

    @utils.log_function_call
    def convert_size_guide(self, product: dict, variant: Variant) -> list[Sizing]:
        # TODO implement
        return []


class FrankAndOakDataConverter(DataConverter):
    def __init__(self):
        super().__init__(shop=constants.Shops.FRANK_AND_OAK.value)

    @utils.log_function_call
    def convert_product(self, product: dict, shop: Shop) -> Product:
        return Product(
            shop=shop,
            brand=product['brand'],
            title=product['title'],
            description=product['description']
        )

    def convert_variant(self, variant: dict, product: Product) -> Variant:
        return Variant(
            product=product,
            image_src=variant['image']['src'],
            link=variant['link'],
            original_price=variant['original_price'],
            final_price=variant['final_price'],
            is_available=variant['available'],
            option1=variant['option1'],
            option2=variant['option2'],
            color=variant['color'],
        )

    @utils.log_function_call
    def convert_size_guide(self, product: dict, variant: Variant) -> list[Sizing]:
        # TODO implement
        return []
