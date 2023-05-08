import json
import logging
import os
import django
from abc import ABC, abstractmethod

from scraper import utils, constants

# Set up the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chicpic.settings")
django.setup()

from clothing.models import Category, Shop, Attribute, Product, ProductAttribute, Variant, SizeGuide


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

    @abstractmethod
    def convert_variant(self, variant: dict, product: Product) -> Variant:
        pass

    @abstractmethod
    def convert_size_guide(self, size_guide_type: str, size_value: str, variant: Variant) -> SizeGuide:
        pass

    @utils.log_function_call
    def convert_category(self, category_title: str, category_gender: str) -> Category:
        # Load shop categories file
        with open(constants.SHOP_CATEGORIES_CONVERTER_FILE_PATH.format(shop_name=self.shop_name), 'r') as f:
            kit_and_ace_categories = json.loads(f.read())

        # Find proper chicpic category similar according to shop categories
        selected_category = None
        for category in kit_and_ace_categories:
            if category['gender'] == category_gender and category['title'] == category_title:
                selected_category = category
                break
        else:
            self.logger.error(f'Proper category not found. title: {category_title}, gender: {category_gender}.')

        if selected_category is not None:
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
    __BRAND_NAME = constants.Shops.KIT_AND_ACE.value.name

    def __init__(self):
        super().__init__(shop=constants.Shops.KIT_AND_ACE.value)

    @utils.log_function_call
    def convert_product(self, product: dict, shop: Shop) -> Product:
        # TODO check if it has more than 1 gender
        category = self.convert_category(product['category'], product['genders'][0])

        return Product(
            shop=shop,
            brand=self.__BRAND_NAME,
            title=product['title'],
            description=product['description'],
            category=category
        )

    def __convert_color(self, color_name: str) -> str:
        file_path = constants.COLORS_CONVERTER_FILE_PATH.format(shop_name=self.shop_name)
        with open(file_path, 'r') as f:
            colors_data = json.loads(f.read())
        return colors_data.get(color_name)

    @utils.log_function_call
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
    def convert_size_guide(self, size_guide_type: str, size_value: str, variant: Variant) -> SizeGuide:
        # TODO implement
        pass
        # file_path = constants.SHOP_SIZE_GUIDES_FILE_PATH.format(shop_name=self._shop_name, size_guide_type=size_guide_type)
        # with open(file_path, 'r') as f:
        #     pass
        # option_choice = utils.find_proper_choice(SizeGuide.SizeGuideOptionChoices.choices, option)
        # SizeGuide(variant=variant, option=option_choice, value=value)
