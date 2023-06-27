import os
from abc import ABC
import requests
import logging
from collections import Counter

from scraper import utils, constants


class ShopifyScraper(ABC):
    def __init__(self, shop: constants.ShopConstant):
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

    def save_products(self, products: list):
        file_path = constants.SCRAPED_PRODUCTS_FILE_PATH.format(shop_name=self.shop.name)
        utils.save_data_file(file_full_path=file_path, data=products)

    @staticmethod
    def get_vendor_counts(products: list) -> Counter:
        return Counter(map(lambda product: product['vendor'], products))

    @staticmethod
    def get_tag_counts(products: list) -> Counter:
        tags = Counter()
        for product in products:
            tags.update(product['tags'])
        return tags

    @staticmethod
    def get_product_type_counts(products: list) -> Counter:
        return Counter(map(lambda product: product['product_type'], products))

    @staticmethod
    def get_attribute_counts(products: list) -> dict:
        product_attributes = dict()

        for product in products:
            for opt_name in list(map(lambda opt: opt['name'], product['options'])):
                if opt_name not in product_attributes.keys():
                    product_attributes[opt_name] = 1
                else:
                    product_attributes[opt_name] += 1

        return product_attributes

    @staticmethod
    def find_all_option_value(products: list, option_name: str) -> Counter:
        sizes = Counter()

        for product in products:
            position = next((opt['position'] for opt in product['options'] if opt['name'] == option_name), None)
            if position is None:
                continue

            for variant in product['variants']:
                sizes[variant[f'option{position}']] += 1

        return sizes

    @utils.log_function_call
    def fetch_products(self):
        products = []
        page = 1

        while True:
            url = f'{self.shop.website}products.json?limit=250&page={page}'
            print(f'Request URL: {url}')
            response = requests.get(url=url)
            data = response.json()

            if len(data.get('products')) == 0:
                break
            else:
                products += data.get('products')
                page += 1

        return products


class KitAndAceScraper(ShopifyScraper):
    SHOP = constants.Shops.KIT_AND_ACE.value

    def __init__(self):
        super().__init__(self.SHOP)


class FrankAndOakScraper(ShopifyScraper):
    SHOP = constants.Shops.FRANK_AND_OAK.value

    def __init__(self):
        super().__init__(self.SHOP)


class TristanScraper(ShopifyScraper):
    SHOP = constants.Shops.TRISTAN.value

    def __init__(self):
        super().__init__(self.SHOP)

