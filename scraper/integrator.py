import importlib
import logging
import os

from django.db import transaction, IntegrityError, DataError
from scraper import constants, scrapers, parsers, converters

from scraper.converters import Product, ProductAttribute, Variant, Sizing


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
        open(constants.LOGS_FILE_PATH.format(module_name='integrator'), 'w').close()
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

                # Soft-Delete products that are not in the parsed file
                Product.objects.filter(
                    shop_id=shop_obj.id
                ).exclude(
                    original_id__in=[p['product_id'] for p in self._parsed_product]
                ).delete()

                for product in self._parsed_product:
                    product_tmp_obj = self._converter.convert_product(product=product, shop=shop_obj)

                    # Check if the product already exists
                    try:
                        product_obj = Product.objects.with_deleted().get(original_id=product_tmp_obj.original_id)
                        # Product already exists, update fields
                        product_obj.brand = product_tmp_obj.brand
                        product_obj.title = product_tmp_obj.title
                        product_obj.description = product_tmp_obj.description

                        # Restore the product if it was soft-deleted
                        if product_obj.is_deleted:
                            product_obj.restore()

                        updated_objects_count['Products'] += 1
                    except Product.DoesNotExist:
                        # Product doesn't exist, create a new one
                        product_obj = product_tmp_obj

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
                        variant_tmp_obj = self._converter.convert_variant(variant=v, product=product_obj)

                        try:
                            variant_obj = Variant.objects.get(original_id=variant_tmp_obj.original_id)
                            # Variant already exists, update fields
                            variant_obj.image_src = variant_tmp_obj.image_src
                            variant_obj.link = variant_tmp_obj.link
                            variant_obj.original_price = variant_tmp_obj.original_price
                            variant_obj.final_price = variant_tmp_obj.final_price
                            variant_obj.is_available = variant_tmp_obj.is_available
                            variant_obj.color_hex = variant_tmp_obj.color_hex
                            variant_obj.size = variant_tmp_obj.size
                            variant_obj.option1 = variant_tmp_obj.option1
                            variant_obj.option2 = variant_tmp_obj.option2
                            updated_objects_count['Variants'] += 1
                        except Variant.DoesNotExist:
                            # Variant doesn't exist, create a new one
                            variant_obj = variant_tmp_obj
                            created_objects_count['Variants'] += 1

                        variant_obj.save()

                        # Handle sizings
                        sizing_tmp_objects = self._converter.convert_sizings(product=product, variant=variant_obj)
                        for sizing_tmp_obj in sizing_tmp_objects:
                            # Check if the sizing already exists
                            try:
                                sizing_obj = Sizing.objects.get(variant=variant_obj, option=sizing_tmp_obj.option)
                                # Sizing already exists, update fields
                                sizing_obj.value = sizing_tmp_obj.value
                                updated_objects_count['Sizings'] += 1
                            except Sizing.DoesNotExist:
                                # Sizing doesn't exist, create a new one
                                sizing_obj = sizing_tmp_obj
                                created_objects_count['Sizings'] += 1

                            sizing_obj.save()

                print("Created Objects:", created_objects_count)
                print("Updated Objects:", updated_objects_count)

        except (IntegrityError, DataError) as error:
            self.logger.exception(error)
        except Exception as error:
            self.logger.exception(error)


if __name__ == '__main__':
    from .utils import get_valid_shop

    selected_shop = get_valid_shop()

    # Dynamically import the classes
    scraper_module = importlib.import_module('scraper.scrapers')
    parser_module = importlib.import_module('scraper.parsers')
    converter_module = importlib.import_module('scraper.converters')

    # Create instances of the classes
    my_integrator = DataIntegrator(
        scraper=getattr(scraper_module, selected_shop['scraper'])(),
        parser=getattr(parser_module, selected_shop['parser'])(),
        converter=getattr(converter_module, selected_shop['converter'])(),
    )

    need_scrape = None
    while need_scrape not in ['y', 'n']:
        need_scrape = input('Do you want to scrape? (y/n): ')

    if need_scrape == 'y':
        print(f'Scraping {selected_shop["name"]}...')
        my_integrator.scrape_save()

    need_parse = None
    while need_parse not in ['y', 'n']:
        print(f'Parsing {selected_shop["name"]}...')
        need_parse = input('Do you want to parse? (y/n): ')

    if need_parse == 'y':
        my_integrator.parse_save()
    else:
        my_integrator.load_parsed_products()

    need_integrate = None
    while need_integrate not in ['y', 'n']:
        print(f'Integrating {selected_shop["name"]}...')
        need_integrate = input('Do you want to integrate? (y/n): ')

    if need_integrate == 'y':
        my_integrator.integrate()
