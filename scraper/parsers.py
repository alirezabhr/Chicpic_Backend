import logging
import os
from abc import ABC, abstractmethod
from collections import Counter

from scrapers import utils, constants


class ShopifyParser(ABC):
    UNACCEPTABLE_PRODUCT_TYPES = None
    UNACCEPTABLE_TAGS = None

    def __init__(self, shop: constants.ShopConstant):
        assert self.UNACCEPTABLE_PRODUCT_TYPES is not None, 'UNACCEPTABLE_PRODUCT_TYPES is None'
        assert self.UNACCEPTABLE_TAGS is not None, 'UNACCEPTABLE_TAGS is None'

        # Make unaccepted tags and unacceptable product types lowercase
        self.UNACCEPTABLE_TAGS = [tag.lower() for tag in self.UNACCEPTABLE_TAGS]
        self.UNACCEPTABLE_PRODUCT_TYPES = [product_type.lower() for product_type in self.UNACCEPTABLE_PRODUCT_TYPES]

        self.shop = shop
        self.__config_logger()

    def __config_logger(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        log_file_formatter = logging.Formatter(
            fmt=f"%(levelname)s %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Create log file if it does not exist
        if not os.path.isdir(constants.LOGS_DIR):
            os.makedirs(constants.LOGS_DIR)

        log_file_path = constants.LOGS_FILE_PATH.format(module_name='parsers')

        if not os.path.exists(log_file_path):
            open(log_file_path, "w").close()

        # Add a file handler to the logger
        file_handler = logging.FileHandler(filename=log_file_path)
        file_handler.setFormatter(log_file_formatter)
        file_handler.setLevel(level=logging.INFO)
        self.logger.addHandler(file_handler)

    def read_parsed_file_data(self):
        return utils.read_data_json_file(constants.PARSED_PRODUCTS_FILE_PATH.format(shop_name=self.shop.name))

    def save_products(self, products: list):
        file_path = constants.PARSED_PRODUCTS_FILE_PATH.format(shop_name=self.shop.name)
        utils.save_data_file(file_full_path=file_path, data=products)

    @staticmethod
    def parsed_product_attribute_position(product: dict, attribute_name: str):
        attribute = list(filter(lambda attr: attr['name'] == attribute_name, product['attributes']))
        return attribute[0]['position'] if len(attribute) > 0 else None

    @staticmethod
    def get_size_guide_counts(parsed_products: list) -> Counter:
        return Counter(map(lambda product: product['size_guide'], parsed_products))

    @utils.log_function_call
    def _product_brand(self, product: dict) -> str:
        return product['vendor']

    @abstractmethod
    def _product_description(self, product: dict):
        return utils.remove_html_tags(product['body_html'])

    @utils.log_function_call
    @abstractmethod
    def _parse_variants(self, product: dict):
        pass

    @utils.log_function_call
    def _parse_attributes(self, product: dict):
        attributes = []
        position = 1

        for opt in product['options']:
            if opt['name'] == 'Color':
                continue
            attributes.append({'name': opt['name'], 'position': position})
            position += 1

        return attributes

    @utils.log_function_call
    def is_unacceptable_product(self, product: dict) -> bool:
        if product['product_type'].lower() in self.UNACCEPTABLE_PRODUCT_TYPES:
            return True
        if any(tag.lower() in self.UNACCEPTABLE_TAGS for tag in product['tags']):
            return True
        return False

    def _product_title(self, product: dict) -> str:
        return product['title']

    @utils.log_function_call
    @abstractmethod
    def _product_genders(self, product: dict) -> list:
        pass

    @utils.log_function_call
    @abstractmethod
    def _product_size_guide(self, product: dict):
        pass

    @utils.log_function_call
    @abstractmethod
    def _product_categories(self, product: dict) -> tuple:
        pass

    @utils.log_function_call
    def _parse_product(self, product: dict):
        return {
            'product_id': product['id'],
            'title': self._product_title(product),
            'categories': self._product_categories(product),
            'description': self._product_description(product),
            'tags': product['tags'],
            'brand': self._product_brand(product),
            'size_guide': self._product_size_guide(product),
            'genders': self._product_genders(product),
            'variants': self._parse_variants(product),
            'attributes': self._parse_attributes(product),
        }

    @utils.log_function_call
    def parse_products(self, scraped_products: list):
        parsed_products = []

        for product in scraped_products:
            if self.is_unacceptable_product(product):
                self.logger.info(f'Product is unacceptable. Product ID: {product["id"]}.')
                continue

            try:
                parsed = self._parse_product(product)
                parsed_products.append(parsed)
            except Exception as error:
                self.logger.exception(f'Product {product["id"]}, ERROR: {error}')
                continue

        return parsed_products


class KitAndAceParser(ShopifyParser):
    UNACCEPTABLE_PRODUCT_TYPES = ['Scarves', 'Underwear & Socks', 'Gift Cards', 'Hats']
    UNACCEPTABLE_TAGS = ['Accessories']

    def __init__(self):
        super().__init__(shop=constants.Shops.KIT_AND_ACE.value)

    def _get_color_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Color':
                return opt['position']
        return None

    def _get_size_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Size':
                return opt['position']
        return None

    def _product_categories(self, product: dict) -> tuple:
        return (product['product_type'],)

    def _product_genders(self, product: dict) -> list:
        genders = set()
        for tag in product['tags']:
            if tag.lower().find("women") != -1:
                genders.add('Women')
            elif tag.lower().find("men") != -1:
                genders.add('Men')

        if len(genders) == 0:
            raise Exception("Can not find product gender.")

        return list(genders)

    def _product_size_guide(self, product: dict):
        size_guide_text = 'SizeGuide::'
        for tag in product['tags']:
            if tag.find(size_guide_text) != -1:
                return tag[len(size_guide_text):]
        return None

    def _parse_variants(self, product: dict):
        product_variants = product['variants']
        available_positions = [1, 2, 3]

        color_opt_position = self._get_color_option_position(product)
        size_opt_position = self._get_size_option_position(product)

        if color_opt_position is not None:
            available_positions.remove(color_opt_position)
        if size_opt_position is not None:
            available_positions.remove(size_opt_position)

        variants = []
        for variant in product_variants:
            color_hex = None if color_opt_position is None else variant[f'option{color_opt_position}']
            size = None if size_opt_position is None else variant[f'option{size_opt_position}']
            option1 = variant[f'option{available_positions[0]}']

            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': variant['compare_at_price'],
                'final_price': variant['price'],
                'option1': option1,
                'option2': None,
                'color_hex': color_hex,
                'size': size,
                'link': f'{self.shop.website}products/{product["handle"]}?variant={variant["id"]}',
            }

            featured_image = variant.get('featured_image')
            if featured_image is None:
                self.logger.warning(
                    f'featured image is NULL. product id: {v["product_id"]}. variant id: {v["variant_id"]}')
                continue
            else:
                v['image'] = {
                    'width': featured_image['width'],
                    'height': featured_image['height'],
                    'src': featured_image['src'],
                }

            variants.append(v)

        return variants


class FrankAndOakParser(ShopifyParser):
    UNACCEPTABLE_PRODUCT_TYPES = ['', 'Lifestyle', 'Bodywear', 'Swimwear', 'Accessories', 'Gift Card', 'Grooming']
    UNACCEPTABLE_TAGS = []

    def __init__(self):
        super().__init__(shop=constants.Shops.FRANK_AND_OAK.value)

    def is_unacceptable_product(self, product: dict) -> bool:
        if len(self._product_genders(product)) > 1:
            return True  # Remove products with more than 1 gender because of confusion in frank & oak size guide
        return super().is_unacceptable_product(product)

    def _product_categories(self, product: dict):
        return (product['product_type'],)

    def _product_genders(self, product: dict) -> list:
        division_key = 'division:'
        division_tags = list(
            map(lambda t2: t2[len(division_key):], filter(lambda t: division_key in t, product['tags'])))

        genders = []
        for tag in division_tags:
            if tag == 'Men':
                genders.append('Men')
            elif tag == 'Women':
                genders.append('Women')

        return genders

    def _product_size_guide(self, product: dict):
        genders = self._product_genders(product)
        if len(genders) == 0:
            return None
        return f"{genders[0]}-{product['product_type']}"

    def _parse_variants(self, product: dict):
        product_variants = product['variants']
        variants = []
        available_positions = [1, 2, 3]

        color_hex = self._product_color(product)
        size_opt_position = self._get_size_option_position(product)
        if size_opt_position is not None:
            available_positions.remove(size_opt_position)

        for variant in product_variants:
            final_price = float(variant['price'])
            original_price = float(variant['compare_at_price'])
            if original_price < final_price:
                original_price = final_price

            size = None if size_opt_position is None else variant[f'option{size_opt_position}']
            option1 = variant[f'option{available_positions[0]}']
            option2 = variant[f'option{available_positions[1]}']

            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': original_price,
                'final_price': final_price,
                'option1': option1,
                'option2': option2,
                'color_hex': color_hex,
                'size': size,
                'link': f'{self.shop.website}products/{product["handle"]}',
            }

            image = product['images'][0]
            v['image'] = {
                'width': image['width'],
                'height': image['height'],
                'src': image['src'],
            }

            variants.append(v)

        return variants

    def _get_size_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Size':
                return opt['position']
        return None

    def _product_color(self, product: dict):
        tag_key = 'color_hex:'
        hex_color_tag = list(filter(lambda tag: tag[:len(tag_key)] == tag_key, product['tags']))

        if len(hex_color_tag) == 0:
            return None

        hex_color = hex_color_tag[-1][len(tag_key):]
        if hex_color == '000':
            hex_color = '000000'

        return hex_color


class TristanParser(ShopifyParser):
    UNACCEPTABLE_PRODUCT_TYPES = None
    UNACCEPTABLE_TAGS = []
    PRODUCT_TYPES = None

    def __init__(self):
        shop = constants.Shops.TRISTAN.value
        # initialize product types
        file_path = constants.SHOP_PRODUCT_TYPES_FILE_PATH.format(shop_name=shop.name)
        self.PRODUCT_TYPES = utils.read_data_json_file(file_path=file_path)
        assert self.PRODUCT_TYPES is not None, "PRODUCT_TYPES is None"
        assert len(self.PRODUCT_TYPES) > 0, "PRODUCT_TYPES is empty"

        self.UNACCEPTABLE_PRODUCT_TYPES = list(filter(lambda key: not self.PRODUCT_TYPES[key]['is_acceptable'],
                                                      self.PRODUCT_TYPES.keys()))
        super().__init__(shop=shop)

    def _product_description(self, product: dict):
        return ''

    def _product_genders(self, product: dict) -> list:
        return [self.PRODUCT_TYPES[product['product_type']]['gender']]

    def _product_categories(self, product: dict) -> tuple:
        return (self.PRODUCT_TYPES[product['product_type']]['category'],)

    def _product_size_guide(self, product: dict):
        return self.PRODUCT_TYPES[product['product_type']]['size_guide']

    def _parse_variants(self, product: dict):
        product_variants = product['variants']
        available_positions = [1, 2, 3]

        color_opt_position = self._get_color_option_position(product)
        size_opt_position = self._get_size_option_position(product)

        if color_opt_position is not None:
            available_positions.remove(color_opt_position)
        if size_opt_position is not None:
            available_positions.remove(size_opt_position)

        variants = []
        for variant in product_variants:
            color_code = None if color_opt_position is None else variant[f'option{color_opt_position}']
            size = None if size_opt_position is None else variant[f'option{size_opt_position}']
            option1 = variant[f'option{available_positions[0]}']

            color_hex = None
            if color_code is not None:
                data = utils.read_data_json_file(constants.COLORS_CONVERTER_FILE_PATH.format(shop_name=self.shop.name))
                color_hex = next((color['hex'] for color in data if color['code'] == color_code[:2]), None)

            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': variant['compare_at_price'],
                'final_price': variant['price'],
                'option1': option1,
                'option2': None,
                'color_hex': color_hex,
                'size': size,
                'link': f'{self.shop.website}products/{product["handle"]}?variant={variant["id"]}',
            }

            image = product['images'][0]
            v['image'] = {
                'width': image['width'],
                'height': image['height'],
                'src': image['src'],
            }

            variants.append(v)

        return variants

    def parse_products(self, scraped_products: list):
        scraped_product_types = set(map(lambda p: p['product_type'], scraped_products))
        current_product_types = set(self.PRODUCT_TYPES.keys())
        assert current_product_types == scraped_product_types, scraped_product_types.difference(current_product_types)
        return super().parse_products(scraped_products)

    def _get_color_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Color' or opt['name'] == 'Colour':
                return opt['position']
        return None

    def _get_size_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Size':
                return opt['position']
        return None


class ReebokParser(ShopifyParser):
    UNACCEPTABLE_PRODUCT_TYPES = ['BOYS', 'GIRLS', 'Gift Cards']
    UNACCEPTABLE_TAGS = ['accessories', 'CAP', 'HEADWEAR', 'HAT', 'socks', 'SOCKS', 'CREW SOCKS', 'ANKLE SOCKS', 'BAG',
                         'GLOVES', 'BRA', 'BOTTLE', 'UNDERWEAR']
    ACCEPTABLE_CATEGORIES = {
        'Shoes': ('shoes', 'shoe', 'sandal', 'sandals-shoes'),
        'Tops': ('t-shirt', 't-shirts', 'tops-t-shirts', 'shirt', 'tank', 'dress', 'leotard'),
        'Outerwear': ('sweatshirt', 'sweatshirts', 'jacket', 'outdoor', 'windbreaker', 'hoodie', 'track top'),
        'Bottoms': ('pant', 'pants', 'short', 'shorts', 'tights', 'leggings', 'skirt'),
    }

    def __init__(self):
        super().__init__(shop=constants.Shops.REEBOK.value)

    def _product_title(self, product: dict) -> str:
        title = product['title']

        # Remove vendor name from title
        vendor = product['vendor']
        if title.lower().startswith(vendor.lower()):
            title = title[len(vendor):]

        # Remove color from title
        colors = [tag[8:] for tag in product['tags'] if tag.startswith('Colour: ')]
        colors.sort(key=lambda c: len(c), reverse=True)
        for color in colors:
            if title.lower().endswith(color.lower()):
                title = title[:-len(color)]
                break

        # Remove trailing spaces
        return title.strip()

    def _product_genders(self, product: dict) -> list:
        pass

        genders = set()

        gender_tags = [tag[8:] for tag in product['tags'] if tag.startswith('Gender: ')]

        if 'Women' in gender_tags:
            genders.add('Women')
        if 'Men' in gender_tags:
            genders.add('Men')
        if 'UNISEX' in gender_tags:
            genders.add('Women')
            genders.add('Men')

        return list(genders)

    def _product_description(self, product: dict):
        description = super()._product_description(product)
        features = [tag[9:] for tag in product['tags'] if tag.startswith('Feature: ')]

        for feature in features:
            description += f'\n{feature}'

        return description

    def is_unacceptable_product(self, product: dict) -> bool:
        if super().is_unacceptable_product(product):
            return True

        if any(word.lower() in self.UNACCEPTABLE_TAGS for word in product['title'].split()):
            return True

        return False

    def _parse_variants(self, product: dict):
        product_variants = product['variants']
        available_positions = [1, 2, 3]

        size_opt_position = self._get_size_option_position(product)
        if size_opt_position is not None:
            available_positions.remove(size_opt_position)

        color_hex = self._get_color_hex(product)

        variants = []
        for variant in product_variants:
            size = None if size_opt_position is None else variant[f'option{size_opt_position}']
            option1 = variant[f'option{available_positions[0]}']

            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': variant['compare_at_price'],
                'final_price': variant['price'],
                'option1': option1,
                'option2': None,
                'color_hex': color_hex,
                'size': size,
                'link': f'{self.shop.website}products/{product["handle"]}?variant={variant["id"]}',
            }

            image = product['images'][0]
            v['image'] = {
                'width': image['width'],
                'height': image['height'],
                'src': image['src'],
            }

            variants.append(v)

        return variants

    def _product_categories(self, product: dict) -> tuple:
        categories = set()
        acceptable_cats = {category for categories in self.ACCEPTABLE_CATEGORIES.values() for category in categories}

        for tag in product['tags']:
            if tag.lower() in acceptable_cats:
                categories.add(tag)

        if len(categories) == 0:
            for word in product['title'].split():
                if word.lower() in acceptable_cats:
                    categories.add(word)

        return tuple(categories)

    def _product_size_guide(self, product: dict):
        pass

    def _get_color_hex(self, product: dict):
        color_tags = [tag[-6:] for tag in product['tags'] if tag.startswith('#')]
        if len(color_tags) > 0:
            return color_tags[0]

    def _get_size_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Size':
                return opt['position']
        return None
