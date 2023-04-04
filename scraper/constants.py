from enum import Enum

SIZE_GUIDE = '{shop_name}::{type}'
SCRAPED_PRODUCTS_FILE_NAME = '{shop_name}__products.json'
PARSED_PRODUCTS_FILE_NAME = '{shop_name}__parsed.json'


class Shops(Enum):
    KIT_AND_ACE = 'Kit and Ace'
