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
        pass

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
    @abstractmethod
    def is_unacceptable_product(self, product: dict) -> bool:
        pass

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
            'title': product['title'],
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

    def is_unacceptable_product(self, product: dict) -> bool:
        if product['product_type'] in self.UNACCEPTABLE_PRODUCT_TYPES:
            return True
        for unacceptable_tag in self.UNACCEPTABLE_TAGS:
            if unacceptable_tag in product['tags']:
                return True
        return False

    def _get_color_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Color':
                return opt['position']
        return None

    def _product_categories(self, product: dict) -> tuple:
        return (product['product_type'],)

    def _product_description(self, product: dict):
        return utils.remove_html_tags(product['body_html'])

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
        color_opt_position = self._get_color_option_position(product)

        variants = []
        for variant in product_variants:
            color = None
            option1 = variant['option1']
            option2 = variant['option2']

            if color_opt_position is not None:
                color = variant[f'option{color_opt_position}']

                if color_opt_position == 1:
                    option1 = variant['option2']
                    option2 = variant['option3']
                elif color_opt_position == 2:
                    option1 = variant['option1']
                    option2 = variant['option3']

            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': variant['compare_at_price'],
                'final_price': variant['price'],
                'option1': option1,
                'option2': option2,
                'color': color,
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
        if product['product_type'] in self.UNACCEPTABLE_PRODUCT_TYPES:
            return True
        if len(self._product_genders(product)) > 1:
            return True  # Remove products with more than 1 gender because of confusion in frank & oak size guide
        return False

    def _product_categories(self, product: dict):
        return (product['product_type'],)

    def _product_description(self, product: dict):
        return utils.remove_html_tags(product['body_html'])

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
        color = self._product_color(product)
        for variant in product_variants:
            final_price = float(variant['price'])
            original_price = float(variant['compare_at_price'])
            if original_price < final_price:
                original_price = final_price

            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': original_price,
                'final_price': final_price,
                'option1': variant['option1'],
                'option2': variant['option2'],
                'color': color,
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

    def _product_color(self, product: dict):
        tag_key = 'color_hex:'
        hex_color_tag = list(filter(lambda tag: tag[:len(tag_key)] == tag_key, product['tags']))

        if len(hex_color_tag) == 0:
            return None

        hex_color = hex_color_tag[-1][len(tag_key):]
        if hex_color == '000':
            hex_color = '000000'

        return hex_color
