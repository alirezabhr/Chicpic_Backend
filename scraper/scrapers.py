import os
from abc import ABC, abstractmethod
import requests
import logging

from scraper import utils, constants


class ShopifyScraper(ABC):
    def __init__(self, shop: constants.ShopConstant):
        self.shop = shop
        self._products = []
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

        log_file_path = constants.LOGS_FILE_PATH.format(module_name='scrapers')

        if not os.path.exists(log_file_path):
            open(log_file_path, "w").close()

        # Add a file handler to the logger
        file_handler = logging.FileHandler(filename=log_file_path)
        file_handler.setFormatter(log_file_formatter)
        file_handler.setLevel(level=logging.INFO)
        self.logger.addHandler(file_handler)

    def read_scraped_file_data(self):
        return utils.read_data_json_file(constants.SCRAPED_PRODUCTS_FILE_PATH.format(shop_name=self.shop.name))

    def read_parsed_file_data(self):
        return utils.read_data_json_file(constants.PARSED_PRODUCTS_FILE_PATH.format(shop_name=self.shop.name))

    @staticmethod
    def parsed_product_attribute_position(product: dict, attribute_name: str):
        attribute = list(filter(lambda attr: attr['name'] == attribute_name, product['attributes']))
        return attribute[0]['position'] if len(attribute) > 0 else None

    def find_all_product_types(self) -> set:
        if len(self._products) == 0:
            self.fetch_products()

        product_types = set()
        for product in self._products:
            if product['product_type'] not in product_types:
                product_types.add(product['product_type'])

        file_path = constants.SHOP_CATEGORIES_FILE_PATH.format(shop_name=self.shop.name)
        utils.save_data_file(file_full_path=file_path, data=list(product_types))

        return product_types

    def find_all_product_attributes(self) -> set:
        if len(self._products) == 0:
            self.fetch_products()

        product_attributes = set()
        for product in self._products:
            for opt_name in list(map(lambda opt: opt['name'], product['options'])):
                product_attributes.add(opt_name)

        return product_attributes

    @utils.log_function_call
    def fetch_products(self):
        self._products = []
        page = 1

        while True:
            url = f'{self.shop.website}products.json?limit=250&page={page}'
            print(f'Request URL: {url}')
            response = requests.get(url=url)
            data = response.json()

            if len(data.get('products')) == 0:
                break
            else:
                self._products += data.get('products')
                page += 1

        return self._products

    def save_products(self, products: list, is_parsed: bool):
        if is_parsed:
            file_path = constants.PARSED_PRODUCTS_FILE_PATH.format(shop_name=self.shop.name)
        else:
            file_path = constants.SCRAPED_PRODUCTS_FILE_PATH.format(shop_name=self.shop.name)

        utils.save_data_file(file_full_path=file_path, data=products)

    def load_products(self, products: list):
        self._products = products

    @utils.log_function_call
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
    def _is_unacceptable_product(self, product: dict) -> bool:
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
    def _parse_product(self, product: dict):
        return {
            'product_id': product['id'],
            'title': product['title'],
            'category': product['product_type'],
            'description': self._product_description(product),
            'tags': product['tags'],
            'size_guide': self._product_size_guide(product),
            'genders': self._product_genders(product),
            'variants': self._parse_variants(product),
            'attributes': self._parse_attributes(product),
        }

    @utils.log_function_call
    def parse_products(self):
        parsed_products = []

        for product in self._products:
            if self._is_unacceptable_product(product):
                self.logger.info(f'Product is unacceptable. Product ID: {product["id"]}.')
                continue

            try:
                parsed = self._parse_product(product)
                parsed_products.append(parsed)
            except Exception as error:
                self.logger.exception(f'Product {product["id"]}, ERROR: {error}')
                continue

        return parsed_products


class KitAndAceScraper(ShopifyScraper):
    UNACCEPTABLE_PRODUCT_TYPES = ['Scarves', 'Underwear & Socks', 'Gift Cards', 'Hats']
    UNACCEPTABLE_TAGS = ['Accessories']

    def __init__(self):
        super().__init__(shop=constants.Shops.KIT_AND_ACE.value)

    def _is_unacceptable_product(self, product: dict) -> bool:
        if product['product_type'] in self.UNACCEPTABLE_PRODUCT_TYPES:
            return True
        for unacceptable_tag in self.UNACCEPTABLE_TAGS:
            if unacceptable_tag in product['tags']:
                return True
        return False

    @staticmethod
    def get_color_option_position(product: dict):
        for opt in product['options']:
            if opt['name'] == 'Color':
                return opt['position']
        return None

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
        color_opt_position = self.get_color_option_position(product)

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


class FrankAndOakScraper(ShopifyScraper):
    UNACCEPTABLE_PRODUCT_TYPES = ['', 'Lifestyle', 'Bodywear', 'Swimwear', 'Accessories', 'Gift Card', 'Grooming']
    UNACCEPTABLE_TAGS = []

    def __init__(self):
        super().__init__(shop=constants.Shops.FRANK_AND_OAK.value)

    def _is_unacceptable_product(self, product: dict) -> bool:
        if product['product_type'] in self.UNACCEPTABLE_PRODUCT_TYPES:
            return True
        if len(self._product_genders(product)) > 1:
            return True  # Remove products with more than 1 gender because of confusion in frank & oak size guide
        return False

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
        color = self.product_color(product)
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

    @staticmethod
    def product_color(product: dict):
        tag_key = 'color_hex:'
        hex_color_tag = list(filter(lambda tag: tag[:len(tag_key)] == tag_key, product['tags']))

        if len(hex_color_tag) == 0:
            return None

        hex_color = hex_color_tag[-1][len(tag_key):]
        if hex_color == '000':
            hex_color = '000000'

        return hex_color
