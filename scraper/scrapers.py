import os
import importlib
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
        utils.save_data_file(file_relative_path=file_path, data=products)

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
    def get_attribute_counts(products: list) -> Counter:
        c = Counter()
        for product in products:
            for opt in product['options']:
                c.update([opt['name']])
        return c

    @staticmethod
    def get_all_option_value(products: list, option_name: str) -> Counter:
        values = Counter()

        for product in products:
            position = next((opt['position'] for opt in product['options'] if opt['name'] == option_name), None)
            if position is None:
                continue

            for variant in product['variants']:
                values[variant[f'option{position}']] += 1

        return values

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


class ReebokScraper(ShopifyScraper):
    SHOP = constants.Shops.REEBOK.value

    def __init__(self):
        super().__init__(self.SHOP)


class PajarScraper(ShopifyScraper):
    SHOP = constants.Shops.PAJAR.value

    def __init__(self):
        super().__init__(self.SHOP)


class VessiScraper(ShopifyScraper):
    SHOP = constants.Shops.VESSI.value

    def __init__(self):
        super().__init__(self.SHOP)


class KeenScraper(ShopifyScraper):
    SHOP = constants.Shops.KEEN.value

    def __init__(self):
        super().__init__(self.SHOP)


if __name__ == '__main__':
    from .utils import get_valid_shop

    selected_shop = get_valid_shop()

    # Dynamically import the classes
    scraper_module = importlib.import_module('scraper.scrapers')
    scraper_cls = getattr(scraper_module, selected_shop['scraper'])()

    need_scrape = None
    while need_scrape not in ['y', 'n']:
        need_scrape = input('Do you want to scrape? (y/n): ')

    if need_scrape == 'y':
        print(f'Scraping {selected_shop["name"]}...')
        scraper_cls.save_products(scraper_cls.fetch_products())

    selected_shop_products = scraper_cls.read_scraped_file_data()

    # Check if user needs vendor counts
    need_vendor_counts = None
    while need_vendor_counts not in ['y', 'n']:
        need_vendor_counts = input('get_vendor_counts? (y/n): ')

    if need_vendor_counts == 'y':
        print(f'get_vendor_counts {selected_shop["name"]}', scraper_cls.get_vendor_counts(selected_shop_products),
              sep='\n', end='\n\n')

    # Check if user needs product type counts
    need_product_type_counts = None
    while need_product_type_counts not in ['y', 'n']:
        need_product_type_counts = input('get_product_type_counts? (y/n): ')

    if need_product_type_counts == 'y':
        print(f'get_product_type_counts {selected_shop["name"]}',
              scraper_cls.get_product_type_counts(selected_shop_products), sep='\n', end='\n\n')

    # Check if user needs tag counts
    need_tag_counts = None
    while need_tag_counts not in ['y', 'n']:
        need_tag_counts = input('get_tag_counts? (y/n): ')

    if need_tag_counts == 'y':
        print(f'get_tag_counts {selected_shop["name"]}', scraper_cls.get_tag_counts(selected_shop_products), sep='\n',
              end='\n\n')

    # Check if user needs tag counts
    need_attribute_counts = None
    while need_attribute_counts not in ['y', 'n']:
        need_attribute_counts = input('get_attribute_counts? (y/n): ')

    if need_attribute_counts == 'y':
        print(f'get_attribute_counts {selected_shop["name"]}', scraper_cls.get_attribute_counts(selected_shop_products),
              sep='\n', end='\n\n')
