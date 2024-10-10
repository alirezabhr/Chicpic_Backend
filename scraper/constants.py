import os
from enum import Enum

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGS_DIR = os.path.join(BASE_DIR, 'logs')
LOGS_FILE_PATH = os.path.join(LOGS_DIR, '{module_name}.log')

DATA_DIR = os.path.join(BASE_DIR, 'data')
SHOP_CATEGORIES_FILE_NAME = 'categories.json'
SCRAPED_PRODUCTS_FILE_NAME = 'scraped_products.json'
PARSED_PRODUCTS_FILE_NAME = 'parsed_product.json'
SCRAPED_PRODUCTS_FILE_PATH = os.path.join(DATA_DIR, '{shop_name}', SCRAPED_PRODUCTS_FILE_NAME)
PARSED_PRODUCTS_FILE_PATH = os.path.join(DATA_DIR, '{shop_name}', PARSED_PRODUCTS_FILE_NAME)
SHOP_CATEGORIES_FILE_PATH = os.path.join(DATA_DIR, '{shop_name}', SHOP_CATEGORIES_FILE_NAME)

FIXTURES_DIR = os.path.join(BASE_DIR, 'fixtures')
CATEGORIES_CONVERTER_DIR = os.path.join(FIXTURES_DIR, 'categories')
SHOP_CATEGORIES_CONVERTER_FILE_PATH = os.path.join(CATEGORIES_CONVERTER_DIR, '{shop_name}.json')
COLORS_CONVERTER_DIR = os.path.join(FIXTURES_DIR, 'colors')
COLORS_CONVERTER_FILE_PATH = os.path.join(COLORS_CONVERTER_DIR, '{shop_name}.json')
SHOP_SIZE_GUIDES_DIR = os.path.join(FIXTURES_DIR, 'shop_size_guides')
SHOP_SIZE_GUIDES_FILE_PATH = os.path.join(SHOP_SIZE_GUIDES_DIR, '{shop_name}', '{size_guide_type}.csv')
SHOP_PRODUCT_TYPES_DIR = os.path.join(FIXTURES_DIR, 'product_types')
SHOP_PRODUCT_TYPES_FILE_PATH = os.path.join(SHOP_PRODUCT_TYPES_DIR, '{shop_name}.json')


class ShopConstant:
    def __init__(self, name: str, website: str):
        self.name = name
        self.website = website

    def __str__(self):
        return self.name


class Shops(Enum):
    KIT_AND_ACE = ShopConstant(name='Kit and Ace', website='https://www.kitandace.com/')
    FRANK_AND_OAK = ShopConstant(name='Frank and Oak', website='https://ca.frankandoak.com/')
    TRISTAN = ShopConstant(name='Tristan', website='https://www.tristanstyle.com/')
    REEBOK = ShopConstant(name='Reebok', website='https://www.reebok.ca/')
    PAJAR = ShopConstant(name='Pajar', website='https://ca.pajar.com/')
    VESSI = ShopConstant(name='Vessi', website='https://ca.vessi.com/')
    KEEN = ShopConstant(name='Keen', website='https://www.keenfootwear.ca/')
    PSYCHO_BUNNY = ShopConstant(name='Psycho Bunny', website='https://www.psychobunny.ca/')
