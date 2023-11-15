import logging
import os

from django.db import transaction, IntegrityError, DataError
from scraper import constants, scrapers, parsers, converters

from scraper.converters import Product, ProductAttribute, Variant


class DataIntegrator:
    def __init__(self, scraper: scrapers.ShopifyScraper, parser: parsers.ShopifyParser,
                 converter: converters.DataConverter):
        self._scraper = scraper
        self._parser = parser
        self._converter = converter
        self._parsed_product = []
        self.__config_logger()

    def __config_logger(self):
        os.makedirs(constants.LOGS_DIR, exist_ok=True)
        # create the file if not exists
        open(constants.LOGS_FILE_PATH.format(module_name='integrator'), 'a').close()
        handler = logging.FileHandler(constants.LOGS_FILE_PATH.format(module_name='integrator'))
        formatter = logging.Formatter(
            fmt=f"%(asctime)s %(module)s %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        self.logger = logging.getLogger()
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def load_parsed_products(self):
        self._parsed_product = self._parser.read_parsed_file_data()

    def scrape_save(self):
        scraped_products = self._scraper.fetch_products()
        self._scraper.save_products(scraped_products)

    def parse_save(self):
        scraped_products = self._scraper.read_scraped_file_data()
        self._parsed_product = self._parser.parse_products(scraped_products)
        self._parser.save_products(self._parsed_product)

    def integrate(self):
        created_objects_count = {'Products': 0, 'Product Categories': 0, 'Variants': 0, 'Product Attributes': 0,
                                 'Sizings': 0}
        updated_objects_count = {'Products': 0, 'Product Categories': 0, 'Variants': 0, 'Product Attributes': 0,
                                 'Sizings': 0}

        try:
            with transaction.atomic():
                shop_obj = self._converter.shop
                shop_obj.save()

                for product in self._parsed_product:
                    # Check if the product already exists
                    try:
                        product_obj = Product.objects.get(original_id=product['product_id'])
                        # Product already exists, update fields
                        product_obj.brand = product['brand']
                        product_obj.title = product['title']
                        product_obj.description = product['description']
                        product_obj.is_deleted = False  # Reset is_deleted flag
                        updated_objects_count['Products'] += 1
                    except Product.DoesNotExist:
                        # Product doesn't exist, create a new one
                        product_obj = self._converter.convert_product(product=product, shop=shop_obj)
                        created_objects_count['Products'] += 1

                    product_obj.save()

                    # Handle categories
                    categories = self._converter.convert_categories(product)
                    product_obj.categories.clear()
                    product_obj.categories.set(categories)
                    created_objects_count['Product Categories'] += len(categories)

                    # Handle attributes
                    for attr in product.get('attributes'):
                        attribute_obj = self._converter.convert_attribute(attribute_name=attr['name'])
                        attribute_obj.save()

                        product_attribute_obj, created = ProductAttribute.objects.get_or_create(
                            product=product_obj,
                            attribute=attribute_obj,
                            defaults={'position': attr['position']}
                        )

                        if not created:
                            # Update position if the attribute already exists
                            product_attribute_obj.position = attr['position']
                            product_attribute_obj.save()
                            updated_objects_count['Product Attributes'] += 1
                        else:
                            created_objects_count['Product Attributes'] += 1

                    # Handle variants
                    for v in product.get('variants'):
                        try:
                            variant_obj = Variant.objects.get(original_id=v['variant_id'])
                            # Variant already exists, update fields
                            variant_obj.image_src = v['image_src']
                            variant_obj.link = v['link']
                            variant_obj.original_price = v['original_price']
                            variant_obj.final_price = v['final_price']
                            variant_obj.is_available = v['is_available']
                            variant_obj.color_hex = v['color_hex']
                            variant_obj.size = v['size']
                            variant_obj.option1 = v['option1']
                            variant_obj.option2 = v['option2']
                            updated_objects_count['Variants'] += 1
                        except Variant.DoesNotExist:
                            # Variant doesn't exist, create a new one
                            variant_obj = self._converter.convert_variant(variant=v, product=product_obj)
                            created_objects_count['Variants'] += 1

                        variant_obj.save()

                        # Handle sizings
                        sizing_objects = self._converter.convert_sizings(product=product, variant=variant_obj)
                        for sizing_obj in sizing_objects:
                            sizing_obj.save()
                            created_objects_count['Sizings'] += 1

                print("Created Objects:", created_objects_count)
                print("Updated Objects:", updated_objects_count)

        except (IntegrityError, DataError) as error:
            self.logger.exception(error)
        except Exception as error:
            self.logger.exception(error)
