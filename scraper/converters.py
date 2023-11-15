import json
import logging
import os
import csv
import django
from abc import ABC

from scraper import utils, constants

# Set up the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chicpic.settings")
django.setup()

from user.models import GenderChoices
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

        # Create log file if it does not exit
        if not os.path.isdir(constants.LOGS_DIR):
            os.makedirs(constants.LOGS_DIR)

        log_file_path = constants.LOGS_FILE_PATH.format(module_name='converters')

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

    def convert_product_attribute(self, product: Product, attribute: Attribute, position: int) -> ProductAttribute:
        return ProductAttribute(product=product, attribute=attribute, position=position)

    @utils.log_function_call
    def convert_product(self, product: dict, shop: Shop) -> Product:
        return Product(
            original_id=product['product_id'],
            shop=shop,
            brand=product['brand'],
            title=product['title'],
            description=product['description']
        )

    @utils.log_function_call
    def convert_variant(self, variant: dict, product: Product) -> Variant:
        return Variant(
            original_id=variant['variant_id'],
            product=product,
            image_src=variant['image']['src'],
            link=variant['link'],
            original_price=variant['original_price'],
            final_price=variant['final_price'],
            is_available=variant['available'],
            option1=variant['option1'],
            option2=variant['option2'],
            color_hex=variant['color_hex'],
            size=variant['size'],
        )

    @utils.log_function_call
    def convert_categories(self, product: dict) -> list[Category]:
        categories = []

        for cat in product['categories']:
            for gen in product['genders']:
                category = self.convert_category(cat, gen)
                if category:
                    categories.append(category)

        return categories

    @utils.log_function_call
    def get_size_guide(self, sizing_type: str) -> tuple:
        file_path = constants.SHOP_SIZE_GUIDES_FILE_PATH.format(shop_name=self.shop_name, size_guide_type=sizing_type)
        with open(file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            return tuple(reader)

    def _product_option_position(self, product: dict, option_name: str):
        position = next((opt['position'] for opt in product['attributes'] if opt['name'] == option_name), None)
        if position is None:
            raise KeyError(f"Product does not have '{option_name}' attribute.")
        return position

    @utils.log_function_call
    def convert_sizings(self, product: dict, variant: Variant) -> list[Sizing]:
        sizings = []

        if product['size_guide'] is None:
            return []

        size_guide_reader = self.get_size_guide(product['size_guide'])
        selected_row = next((row for row in size_guide_reader if row['Size'] == variant.size), None)

        if selected_row is None:  # Variant size not found in size guide
            return sizings

        selected_row.pop('Size')
        for k, v in selected_row.items():
            try:
                size_option = utils.find_proper_choice(Sizing.SizingOptionChoices.choices, k)

                if v.find('-') != -1:
                    values = list(map(lambda val: float(val), v.split('-')))
                    size_value = sum(values) / len(values)
                elif v.find('/') != -1:
                    values = list(map(lambda val: float(val), v.split('/')))
                    size_value = sum(values) / len(values)
                else:
                    size_value = float(v)
            except:
                continue

            sizings.append(Sizing(variant=variant, option=size_option, value=round(size_value, 1)))

        return sizings

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
            gender = utils.find_proper_choice(GenderChoices.choices, selected_category['gender'])
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

    def __convert_color(self, color_name: str) -> str:
        file_path = constants.COLORS_CONVERTER_FILE_PATH.format(shop_name=self.shop_name)
        with open(file_path, 'r') as f:
            colors_data = json.loads(f.read())
        return colors_data.get(color_name)

    def convert_variant(self, variant: dict, product: Product) -> Variant:
        return Variant(
            original_id=variant['variant_id'],
            product=product,
            image_src=variant['image']['src'],
            link=variant['link'],
            original_price=variant['original_price'],
            final_price=variant['final_price'],
            is_available=variant['available'],
            option1=variant['option1'],
            option2=variant['option2'],
            color_hex=self.__convert_color(variant['color_hex']),
            size=variant['size'],
        )

    def convert_sizings(self, product: dict, variant: Variant) -> list[Sizing]:
        if product['size_guide'] == 'Men-Bottoms':
            variant_size = variant.size

            try:
                length_attr_position = self._product_option_position(product, 'Length')
                variant_length = variant.__dict__.get(f'option{length_attr_position}')[:2]
            except KeyError:
                return super().convert_sizings(product, variant)

            size_guide_reader = self.get_size_guide(product['size_guide'])
            selected_row = next((row for row in size_guide_reader if row['Size'] == variant.size), None)

            if selected_row is None:  # Variant size not found in size guide
                return []

            waist, inseam = list(map(lambda s: round(float(s) * 2.54, 1), (variant_size, variant_length)))
            hips = selected_row.get('Hips')
            return [Sizing(variant=variant, option=Sizing.SizingOptionChoices.WAIST, value=waist),
                    Sizing(variant=variant, option=Sizing.SizingOptionChoices.HIPS, value=hips),
                    Sizing(variant=variant, option=Sizing.SizingOptionChoices.INSEAM, value=inseam)]
        elif product['size_guide'] == 'Women-Bottoms':
            variant_size = variant.size

            if 'T' in variant_size:
                size_guide_reader = self.get_size_guide(product['size_guide'])
                selected_row = next((row for row in size_guide_reader if row['Size'] == variant_size[:-1]), None)

                if selected_row is None:  # Variant size not found in size guide
                    return []

                waist, hips, inseam = [selected_row.get('Waist'), selected_row.get('Hips'),
                                       selected_row.get('Tall Inseam')]
                return [Sizing(variant=variant, option=Sizing.SizingOptionChoices.WAIST, value=waist),
                        Sizing(variant=variant, option=Sizing.SizingOptionChoices.HIPS, value=hips),
                        Sizing(variant=variant, option=Sizing.SizingOptionChoices.INSEAM, value=inseam)]
            else:
                return super().convert_sizings(product, variant)
        else:
            return super().convert_sizings(product, variant)


class FrankAndOakDataConverter(DataConverter):
    def __init__(self):
        super().__init__(shop=constants.Shops.FRANK_AND_OAK.value)

    def convert_sizings(self, product: dict, variant: Variant) -> list[Sizing]:
        variant_size = variant.size

        if product['size_guide'] in ('Men-Footwear', 'Women-Footwear'):
            size_value = round(float(variant_size), 1)
            if size_value > 30: # Convert from EU to US
                return super().convert_sizings(product, variant)
            else:   # Use US size
                return [Sizing(variant=variant, option=Sizing.SizingOptionChoices.SHOE_SIZE, value=size_value)]
        elif product['size_guide'] == 'Men-Bottoms':
            if len(variant_size) > 2 and variant_size[2] == 'X':
                waist, inseam = list(map(lambda s: round(float(s) * 2.54, 1), variant_size.split('X')))
                return [Sizing(variant=variant, option=Sizing.SizingOptionChoices.WAIST, value=waist),
                        Sizing(variant=variant, option=Sizing.SizingOptionChoices.INSEAM, value=inseam)]
            else:
                return super().convert_sizings(product, variant)
        else:
            return super().convert_sizings(product, variant)


class TristanDataConverter(DataConverter):
    def __init__(self):
        super().__init__(shop=constants.Shops.TRISTAN.value)


class ReebokDataConverter(DataConverter):
    def __init__(self):
        super().__init__(shop=constants.Shops.REEBOK.value)

    def convert_sizings(self, product: dict, variant: Variant) -> list[Sizing]:
        if product['size_guide'] in ('Men-Shoes', 'Women-Shoes'):
            variant_size = variant.size
            size_value = round(float(variant_size), 1)
            return [Sizing(variant=variant, option=Sizing.SizingOptionChoices.SHOE_SIZE, value=size_value)]
        else:
            return super().convert_sizings(product, variant)
