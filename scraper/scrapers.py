import os
from abc import ABC, abstractmethod
import json
import requests
import logging

from scraper import utils, constants


class ShopifyScraper(ABC):
    def __init__(self, shop_name: str, base_url: str):
        self.base_url = base_url
        self.shop_name = shop_name
        self._products = []
        self.__config_logger()

    def __config_logger(self):
        self.logger = logging.getLogger(self.shop_name)
        self.logger.setLevel(logging.INFO)
        log_file_formatter = logging.Formatter(
            fmt=f"%(levelname)s %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Create log file if does not exit
        logs_dir = 'logs'
        log_file_name = f'{self.shop_name}.log'
        log_file_path = os.path.join(logs_dir, log_file_name)

        if not os.path.isdir(logs_dir):
            os.makedirs(logs_dir)

        if not os.path.exists(log_file_path):
            open(log_file_path, "w").close()

        # Add a file handler to the logger
        file_handler = logging.FileHandler(filename=log_file_path)
        file_handler.setFormatter(log_file_formatter)
        file_handler.setLevel(level=logging.INFO)
        self.logger.addHandler(file_handler)

    def fetch_products(self):
        self._products = []
        page = 1

        while True:
            response = requests.get(f'{self.base_url}products.json?limit=250&page={page}')
            data = response.json()

            if len(data.get('products')) == 0:
                break
            else:
                self._products += data.get('products')
                page += 1

        return self._products

    def save_products(self, products: list, is_parsed: bool):
        if is_parsed:
            file_name = constants.PARSED_PRODUCTS_FILE_NAME.format(shop_name=self.shop_name)
        else:
            file_name = constants.SCRAPED_PRODUCTS_FILE_NAME.format(shop_name=self.shop_name)

        utils.save_products_data(file_name, json.dumps(products))

    def load_products(self, products: list):
        self._products = products

    @abstractmethod
    def _product_description(self, product: dict):
        pass

    @abstractmethod
    def _parse_variants(self, product: dict):
        pass

    @abstractmethod
    def _is_accessory(self, product: dict) -> bool:
        pass

    @abstractmethod
    def _product_genders(self, product: dict) -> list:
        pass

    @abstractmethod
    def _product_size_guide(self, product: dict):
        pass

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
        }

    def parse_products(self):
        parsed_products = []

        for product in self._products:
            if self._is_accessory(product):
                self.logger.info(f'Product is accessory. Product ID: {product["id"]}.')
                continue

            parsed_products.append(self._parse_product(product))

        return parsed_products


class KitAndAceScraper(ShopifyScraper):
    def __init__(self):
        super().__init__(constants.Shops.KIT_AND_ACE.value, 'https://www.kitandace.com/')

    def _is_accessory(self, product: dict) -> bool:
        for tag in product['tags']:
            if tag == 'Accessories':
                return True
        return False

    def _product_description(self, product: dict):
        return utils.remove_html_tags(product['body_html'])

    def _product_genders(self, product: dict) -> list:
        genders = set()
        for tag in product['tags']:
            if tag.lower().find("men") != -1:
                genders.add('Men')
            elif tag.lower().find("women") != -1:
                genders.add('Women')
        return list(genders)

    def _product_size_guide(self, product: dict):
        size_guide_text = 'SizeGuide::'
        for tag in product['tags']:
            if tag.find(size_guide_text) != -1:
                return constants.SIZE_GUIDE.format(shop_name=self.shop_name, type=tag[len(size_guide_text):])
        return None

    def _parse_variants(self, product: dict):
        product_variants = product['variants']
        product_options = product['options']

        variants = []
        for variant in product_variants:
            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': variant['compare_at_price'],
                'final_price': variant['price'],
                'attributes': dict(),
                'link': f'{self.base_url}products/{product["handle"]}?variant={variant["id"]}',
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

            for opt in product_options:
                v['attributes'][f'{opt["name"]}'] = variant[f'option{opt["position"]}']

            variants.append(v)

        return variants
