import os
from abc import ABC, abstractmethod
import re
import json
import requests
import logging


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
    
    def save_data(self, file_name, data):
        data_dir = 'data'
        file_full_name = f'{self.shop_name}__{file_name}.json'
        file_path = os.path.join(data_dir, file_full_name)

        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)

        with open(file_path, 'w') as f:
            f.write(json.dumps(data))

    def save_products(self):
        self.save_data('products', self._products)

    def load_products(self, products: list):
        self._products = products

    def remove_html_tags(self, html_data: str):
        clean = re.compile('<.*?>')  # compile the regular expression pattern to match HTML tags
        return re.sub(clean, '', html_data)  # remove the matched tags from the input string

    @abstractmethod
    def _parse_product(self, product: dict):
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

    def parse_products(self):
        parsed_products = []

        for product in self._products:
            if self._is_accessory(product):
                self.logger.info(f'Product is accessory. Product ID: {product["id"]}.')
                continue

            parsed = self._parse_product(product)
            parsed['size_guide'] = self._product_size_guide(product)
            parsed['genders'] = self._product_genders(product)
            parsed['variants'] = self._parse_variants(product)

            parsed_products.append(parsed)

        return parsed_products


class KitAndAceScraper(ShopifyScraper):
    def __init__(self):
        super().__init__('Kit And Ace', 'https://www.kitandace.com/')

    def _is_accessory(self, product: dict) -> bool:
        for tag in product['tags']:
            if tag == 'Accessories':
                return True
        return False

    def _product_genders(self, product: dict) -> list:
        genders = []
        for tag in product['tags'].copy():
            if tag == 'Men':
                genders.append('Men')
                product['tags'].remove('Men')
            elif tag == 'Women':
                genders.append('Women')
                product['tags'].remove('Women')
        return genders

    def _product_size_guide(self, product: dict):
        size_guide_text = 'SizeGuide::'
        for tag in product['tags']:
            if tag.find(size_guide_text) != -1:
                product['tags'].remove(tag)
                return f'{self.shop_name}::{tag[len(size_guide_text):]}'
        return None

    def _parse_product(self, product: dict):
        return {
            'product_id': product['id'],
            'title': product['title'],
            'category': product['product_type'],
            'description': self.remove_html_tags(product['body_html']),
            'tags': product['tags'],
        }

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
                self.logger.warning(f'featured image is NULL. product id: {v["product_id"]}. variant id: {v["variant_id"]}')
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
        

if __name__ == '__main__':
    with open('Kit And Ace_parsed_products.json', 'r') as f:
        data = json.loads(f.read())


