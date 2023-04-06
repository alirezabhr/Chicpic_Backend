import os
from enum import Enum

LOGS_DIR = 'logs'
LOGS_FILE_PATH = os.path.join(LOGS_DIR, '{module_name}.log')

DATA_DIR = 'data'
SCRAPED_PRODUCTS_FILE_NAME = '{shop_name}__products.json'
PARSED_PRODUCTS_FILE_NAME = '{shop_name}__parsed.json'

FIXTURES_DIR = 'fixtures'
CATEGORIES_DIR = os.path.join(FIXTURES_DIR, 'categories')
SHOP_CATEGORIES_FILE_PATH = os.path.join(CATEGORIES_DIR, '{shop_name}__categories.json')
SHOP_SIZE_GUIDES_DIR = os.path.join(FIXTURES_DIR, 'shop_size_guide')
SHOP_SIZE_GUIDES_FILE_PATH = os.path.join(SHOP_SIZE_GUIDES_DIR, '{shop_name}', '{size_guide_type}.csv')


class Shops(Enum):
    KIT_AND_ACE = 'Kit and Ace'
