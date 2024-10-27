import json
import logging
import os
from abc import ABC, abstractmethod
from collections import Counter

import requests

from scraper import utils, constants


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
        utils.save_data_file(file_relative_path=file_path, data=products)

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

    @utils.log_function_call
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
            if opt['name'] in ['Color', 'Colour', 'Size']:
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

    # TODO: refactor and fix it
    # @utils.log_function_call
    # @abstractmethod
    # def _variant_size(self, product: dict, variant: dict):
    #     pass
    #
    # @utils.log_function_call
    # @abstractmethod
    # def _variant_color(self, product: dict, variant: dict):
    #     pass

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
    def _get_size_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Size':
                return opt['position']
        return None

    @utils.log_function_call
    def _get_color_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Color':
                return opt['position']
        return None

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
    UNACCEPTABLE_PRODUCT_TYPES = ['', 'Scarves', 'Underwear & Socks', 'Gift Cards', 'Hats', 'Shopping Totes',
                                  'Gloves & Mittens']
    UNACCEPTABLE_TAGS = ['Accessories']

    def __init__(self):
        super().__init__(shop=constants.Shops.KIT_AND_ACE.value)

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
                    'src': featured_image['src'],
                    'width': featured_image['width'],
                    'height': featured_image['height'],
                }

            variants.append(v)

        return variants


class FrankAndOakParser(ShopifyParser):
    UNACCEPTABLE_PRODUCT_TYPES = ['', 'Lifestyle', 'Bodywear', 'Swimwear', 'Accessories', 'Gift Card', 'Grooming',
                                  'Insurance']
    UNACCEPTABLE_TAGS = []

    def __init__(self):
        super().__init__(shop=constants.Shops.FRANK_AND_OAK.value)

    def is_unacceptable_product(self, product: dict) -> bool:
        if len(self._product_genders(product)) > 1:
            return True  # Remove products with more than 1 gender because of confusion in frank & oak size guide
        return super().is_unacceptable_product(product)

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

    def _product_categories(self, product: dict):
        return (product['product_type'],)

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
    UNACCEPTABLE_PRODUCT_TYPES = ['Socks', 'Jewellery', 'Scarves', 'Belts', 'Socks & Tights', 'Sunglasses', 'Hats',
                                  'Ties', 'Bags', 'Underwear', 'Other Accessories', 'Miscellenious']
    UNACCEPTABLE_TAGS = []
    ACCEPTABLE_CATEGORIES = {
        'Shoes': ('Shoes',),
        'Tops': ('T-Shirts', 'Shirts & Blouses', 'Shirts & Overshirts', 'Outerwear', 'Sweaters & Cardigans', 'Blazers',
                 'Dresses', 'Vests'),
        'Bottoms': ('Pants', 'Jeans', 'Skirts'),
    }

    def __init__(self):
        super().__init__(shop=constants.Shops.TRISTAN.value)

    def _product_description(self, product: dict):
        return utils.remove_html_tags(product['body_html']) if product['body_html'] else ''

    def _product_genders(self, product: dict) -> list:
        tags = product['tags']
        labels = [tag[8:] for tag in tags if tag.startswith('__label:')]
        genders = []
        for label in labels:
            if label == 'Men':
                genders.append('Men')
            elif label == 'Women':
                genders.append('Women')
        return genders

    def _product_categories(self, product: dict) -> tuple:
        return (product['product_type'],)

    def _product_size_guide(self, product: dict):
        genders = self._product_genders(product)
        if not genders:
            return None

        categories = self._product_categories(product)
        category = categories[0] if categories else None

        if category:
            for key, value in self.ACCEPTABLE_CATEGORIES.items():
                if category in value:
                    return f'{genders[0]}-{key}'

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
            final_price = float(variant['price'])
            original_price = float(variant['compare_at_price'])
            if original_price < final_price:
                original_price = final_price

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
                'original_price': original_price,
                'final_price': final_price,
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

    def _get_color_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Color' or opt['name'] == 'Colour':
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
        'Bottoms': ('pant', 'pants', 'short', 'shorts', 'leggings', 'tights', 'skirt'),
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

        # TODO: refactor and fix it
        if 'Footwear' in product['vendor']:
            for opt in product['options']:
                if opt['name'] == 'Size':
                    return '/' in opt['values'][0]

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
            final_price = float(variant['price'])
            original_price = float(variant['compare_at_price'])
            if original_price < final_price:
                original_price = final_price

            size = None if size_opt_position is None else variant[f'option{size_opt_position}']
            option1 = variant[f'option{available_positions[0]}']

            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': original_price,
                'final_price': final_price,
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
                categories.add(tag.lower())

        if not categories:
            for word in product['title'].split():
                if word.lower() in acceptable_cats:
                    categories.add(word.lower())

        return tuple(categories)

    def _product_size_guide(self, product: dict):
        genders = self._product_genders(product)
        if not genders:
            return None

        categories = self._product_categories(product)
        category = categories[0] if categories else None

        if category:
            for key, value in self.ACCEPTABLE_CATEGORIES.items():
                if category in value:
                    return f'{genders[0]}-{key}'

        return None

    def _get_color_hex(self, product: dict):
        color_tags = [tag[-6:] for tag in product['tags'] if tag.startswith('#')]
        if len(color_tags) > 0:
            return color_tags[0]


class PajarParser(ShopifyParser):
    UNACCEPTABLE_PRODUCT_TYPES = ['Repair - Heritage', ]
    UNACCEPTABLE_TAGS = ['ACCESSORIES', 'kids', 'fits: Kids', 'BOYS', 'GIRLS', 'pup', 'fits: Pup']

    def __init__(self):
        super().__init__(shop=constants.Shops.PAJAR.value)

    def _product_brand(self, product: dict) -> str:
        return 'Pajar'

    def _product_genders(self, product: dict) -> list:
        split_title = product['title'].lower().split(' ')

        if "men's" in split_title:
            return ['Men']
        elif "women's" in split_title:
            return ['Women']
        else:
            return []

    def _parse_variants(self, product: dict):
        product_variants = product['variants']
        available_positions = [1, 2, 3]

        color_opt_position = self._get_color_option_position(product)
        size_opt_position = self._get_size_option_position(product)

        if color_opt_position is not None:
            available_positions.remove(color_opt_position)
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
                'original_price': variant['compare_at_price'] if variant['compare_at_price'] else variant['price'],
                'final_price': variant['price'],
                'option1': option1,
                'option2': None,
                'color_hex': color_hex,
                'size': size,
                'link': f'{self.shop.website}products/{product["handle"]}?variant={variant["id"]}',
            }

            featured_image = variant.get('featured_image')
            if featured_image is None and len(product['images']) != 0:
                featured_image = product['images'][0]

            v['image'] = {
                'width': featured_image['width'],
                'height': featured_image['height'],
                'src': featured_image['src'],
            }

            variants.append(v)

        return variants

    def _product_categories(self, product: dict) -> tuple:
        if "_tabs_mens-footwear-size-conversion" in product['tags'] \
                or "_tabs_womens-footwear-size-conversion" in product['tags']:
            return ('Footwear',)
        elif "_tabs_mens-outerwear-nude-body-measurements" in product['tags'] \
                or "_tabs_womens-outerwear-nude-body-measurements" in product['tags']:
            return ('Outerwear',)
        else:
            return ()

    def _product_size_guide(self, product: dict):
        if "_tabs_mens-footwear-size-conversion" in product['tags']:
            return 'Men-Footwear'
        elif "_tabs_womens-footwear-size-conversion" in product['tags']:
            return 'Women-Footwear'
        elif "_tabs_mens-outerwear-nude-body-measurements" in product['tags']:
            return 'Men-Outerwear'
        elif "_tabs_womens-outerwear-nude-body-measurements" in product['tags']:
            return 'Women-Outerwear'

    def _get_color_hex(self, product: dict):
        color_opt = list(filter(lambda opt: opt['name'] == 'Color', product['options']))
        if len(color_opt) == 0:
            return None

        color_name = color_opt[0]['values'][0]

        with open(constants.COLORS_CONVERTER_FILE_PATH.format(shop_name=self.shop.name), 'r') as f:
            shop_colors = json.load(f)

        if color_name.upper() in shop_colors:
            if shop_colors[color_name].startswith('#'):
                if '|' in shop_colors[color_name]:
                    # Color value includes multiple hex values
                    return f'{shop_colors[color_name][1:7]}/{shop_colors[color_name][9:15]}'
                else:
                    return shop_colors[color_name][1:]
            else:
                # Color value is not hex. It might be an image url
                return None
        else:
            # Color value is not in the colors converter file
            color_value = self.__write_colors_converter(product)
            if shop_colors[color_name].startswith('#'):
                if '|' in shop_colors[color_name]:
                    # Color value includes multiple hex values
                    return f'{shop_colors[color_name][1:7]}/{shop_colors[color_name][9:15]}'
                else:
                    return shop_colors[color_name][1:]
            else:
                # Color value is not hex. It might be an image url
                return None

    def __write_colors_converter(self, product: dict):
        with open(constants.COLORS_CONVERTER_FILE_PATH.format(shop_name=self.shop.name), 'r') as f:
            shop_colors = json.load(f)

        url = f'https://s-pc.webyze.com/ProductColors/productGroup-pajar-canada6-{product["id"]}.json'
        response = requests.get(url).json()

        if 'error' in response.keys():
            return None

        data = response['data']
        color_value = None
        for item in data:
            shop_colors[item['name']] = item['data']
            if item['id'] == product['id']:
                color_value = item['data']

        with open(constants.COLORS_CONVERTER_FILE_PATH.format(shop_name=self.shop.name), 'w') as f:
            f.write(json.dumps(shop_colors, indent=4))

        return color_value


class VessiParser(ShopifyParser):
    ## Only shoes are acceptable
    UNACCEPTABLE_PRODUCT_TYPES = ['Apparel', 'Socks', '', 'Gloves', 'Bag', 'Donation', 'Hats', 'Face Masks',
                                  'Gift Card']
    UNACCEPTABLE_TAGS = ['Gender: Kids', 'Style: Kids', 'kids', 'Product: Kids Weekend Sale']

    def __init__(self):
        super().__init__(shop=constants.Shops.VESSI.value)

    def _get_size_option_position(self, product: dict):
        for opt in product['options']:
            if opt['name'] == 'Size' or opt['name'] == 'US Size':
                return opt['position']
        return None

    def _product_brand(self, product: dict) -> str:
        return 'Vessi'

    def _product_genders(self, product: dict) -> list:
        if 'Gender: Men' in product['tags'] or 'Style: Men' not in product['tags']:
            return ['Men']
        else:
            return ['Women']

    def _product_categories(self, product: dict) -> tuple:
        ## Only shoes are acceptable
        return ('Footwear',)

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
            size = None if size_opt_position is None else variant[f'option{size_opt_position}']
            if not size.isnumeric():
                # Remove variants with size like "7U" or "6G"
                continue

            option1 = variant[f'option{available_positions[0]}']

            # There is no discount price in data of Vessi
            price = variant['price']

            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': price,
                'final_price': price,
                'option1': option1,
                'option2': None,
                'color_hex': self._get_color_hex(product),
                'size': size,
                'link': f'{self.shop.website}products/{product["handle"]}',
            }

            image = variant.get('featured_image') if variant.get('featured_image') else product['images'][0]
            v['image'] = {
                'width': image['width'],
                'height': image['height'],
                'src': image['src'],
            }

            variants.append(v)

        return variants

    def _product_size_guide(self, product: dict):
        return f'{self._product_genders(product)[0]}-{self._product_categories(product)[0]}'

    def _get_color_hex(self, product: dict):
        with open(constants.COLORS_CONVERTER_FILE_PATH.format(shop_name=self.shop.name), 'r') as f:
            color_map = json.load(f)
        color_tags = list(map(lambda ct: color_map[ct[7:]], filter(lambda t: t.startswith('Color:'), product['tags'])))
        # Up to 3 colors are acceptable
        color_tags = color_tags[:3]
        return "/".join(color_tags)

    def _parse_attributes(self, product: dict):
        attributes = []
        position = 1

        for opt in product['options']:
            if opt['name'] in ['Color', 'Colour', 'Size', 'US Size']:
                continue
            attributes.append({'name': opt['name'], 'position': position})
            position += 1

        return attributes


class KeenParser(ShopifyParser):
    UNACCEPTABLE_PRODUCT_TYPES = ['Accessories']
    UNACCEPTABLE_TAGS = []

    def __init__(self):
        super().__init__(shop=constants.Shops.KEEN.value)

    def is_unacceptable_product(self, product: dict) -> bool:
        if product['product_type'].lower().startswith('kid'):
            return True
        return super().is_unacceptable_product(product)

    def _product_genders(self, product: dict) -> list:
        key = 'gender:'
        genders = list(map(lambda st: st[len(key):], filter(lambda t: t.startswith(key), product['tags'])))
        if 'All Gender' in genders:
            return ['Men', 'Women']
        if genders[0] == "Women's":
            return ['Women']
        if genders[0] == "Men's":
            return ['Men']
        return []

    def _product_categories(self, product: dict) -> tuple:
        return ('Footwear',)

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
            size = None if size_opt_position is None else variant[f'option{size_opt_position}']
            option1 = variant[f'option{available_positions[0]}']

            final_price = variant['price']
            original_price = variant['compare_at_price'] if variant['compare_at_price'] else final_price

            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': original_price,
                'final_price': final_price,
                'option1': option1,
                'option2': None,
                'color_hex': self._get_color_hex(product),
                'size': size,
                'link': f'{self.shop.website}products/{product["handle"]}',
            }

            image = variant.get('featured_image') if variant.get('featured_image') else product['images'][0]
            v['image'] = {
                'width': image['width'],
                'height': image['height'],
                'src': image['src'],
            }

            variants.append(v)

        return variants

    def _get_color_hex(self, product: dict):
        with open(constants.COLORS_CONVERTER_FILE_PATH.format(shop_name=self.shop.name), 'r') as f:
            color_map = json.load(f)
        # Color 'misc' does not load in parsed file
        key = 'filtercolor:'
        colors = list(map(lambda ct: color_map[ct[len(key):]], filter(lambda t: t.startswith(key), product['tags'])))
        # remove null values and limit it to up to 3 items
        colors = [color for color in colors if color is not None][:3]
        return "/".join(colors)

    def _product_size_guide(self, product: dict):
        key = 'size_guide:'
        size_guide = list(map(lambda st: st[len(key):], filter(lambda t: t.startswith(key), product['tags'])))[0]
        if size_guide == 'womens':
            return f'Women-Footwear'
        elif size_guide == 'mens':
            return f'Men-Footwear'
        elif size_guide == 'all gender':
            return f'Men-Footwear'
        else:
            return None


class PsychoBunnyParser(ShopifyParser):
    UNACCEPTABLE_PRODUCT_TYPES = [
        'KIDS POLOS',
        'Accessories',
        'ACCESSORIES'
        'Gift Cards',
        'MENS ACCESSORIES',
        'KIDS ACCESSORIES',
        'KIDS T-SHIRTS',
        '',
        'KIDS SWIMWEAR',
        'KIDS HOODIES',
        'KIDS SWEAT PANTS',
        'KIDS SHORTS',
        'KIDS SWEAT SHORTS',
        'KIDS TOPS',
        'KIDS JACKETS',
        'KIDS SWEATSHIRTS'
        'KIDS PANTS',
        'KIDS SHIRTS',
        ]
    UNACCEPTABLE_TAGS = ['department:Kids']

    def __init__(self):
        super().__init__(shop=constants.Shops.PSYCHO_BUNNY.value)

    def _product_categories(self, product: dict) -> tuple:
        key = 'category:'
        # Filter the tags that start with the 'category:' key
        categories = tuple(map(lambda t2: t2[len(key):], filter(lambda t: t.startswith(key), product['tags'])))
        # If no category tags are found, return the product type as a tuple
        if categories:
            return categories
        return (product['product_type'],)
        
    

    def _product_genders(self, product: dict) -> list:
        division_key = 'department:'
        division_tags = list(
            map(lambda t2: t2[len(division_key):], filter(lambda t: division_key in t, product['tags'])))

        genders = []
        for tag in division_tags:
            if tag == 'Mens':
                genders.append('Men')
            elif tag == 'Womens':
                genders.append('Women')
            
        if genders == []:
            genders.append('Men')
            genders.append('Women') 
        return genders

    def _product_size_guide(self, product: dict):
        genders = self._product_genders(product)
        category = self._product_categories(product) 
        if len(genders) == 0:
            return None
        return f"{genders[0]}-{category[0]}"

    def _parse_variants(self, product: dict):
        product_variants = product['variants']
        variants = []
        available_positions = [1, 2, 3]

        color_opt_position = self._get_color_option_position(product)
        size_opt_position = self._get_size_option_position(product)

        if color_opt_position is not None:
            available_positions.remove(color_opt_position)
        if size_opt_position is not None:
            available_positions.remove(size_opt_position)

        for variant in product_variants:
            # TODO: check if this is correct
            final_price = float(variant['price'])
    
            # If compare_at_price is null, use final_price as the original_price
            original_price = float(variant['compare_at_price']) if variant['compare_at_price'] is not None else final_price

            # Ensure original_price is not less than final_price
            if original_price < final_price:
                original_price = final_price

            
            color_hex = None if color_opt_position is None else variant[f'option{color_opt_position}']
            size = None if size_opt_position is None else variant[f'option{size_opt_position}']
            option1 = variant[f'option{available_positions[0]}']
            # option2 = variant[f'option{available_positions[1]}']

            v = {
                'variant_id': variant['id'],
                'product_id': variant['product_id'],
                'available': variant['available'],
                'original_price': original_price,
                'final_price': final_price,
                # 'price_is_ok': price_is_ok,
                'option1': option1,
                'option2': None,
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
    
    def _product_color(self, product: dict):
        pass