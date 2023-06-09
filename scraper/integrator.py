import json
import logging
from django.db import transaction, IntegrityError, DataError

from scraper import constants
from scraper import scrapers
from scraper import converters


class DataIntegrator:
    def __init__(self, scraper: scrapers.ShopifyScraper, converter: converters.DataConverter,
                 parsed_products: list = None):
        self._scraper = scraper
        self._converter = converter
        self._parsed_products = [] if parsed_products is None else parsed_products
        self.__config_logger()

    def __config_logger(self):
        # TODO create a log file if not exists (file and dir)
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
        with open(constants.PARSED_PRODUCTS_FILE_PATH.format(shop_name=self._converter.shop_name), 'r') as f:
            self._parsed_products = json.loads(f.read())

    def scrape(self):
        scraped_products = self._scraper.fetch_products()
        self._scraper.save_products(scraped_products, False)
        self._parsed_products = self._scraper.parse_products()
        self._scraper.save_products(self._parsed_products, True)

    def integrate(self):
        try:
            with transaction.atomic():
                shop_obj = self._converter.shop
                shop_obj.save()

                for product in self._parsed_products:
                    product_obj = self._converter.convert_product(product=product, shop=shop_obj)
                    product_obj.save()

                    categories = self._converter.convert_categories(product)
                    product_obj.categories.set(categories)

                    for attr in product.get('attributes'):
                        # Create or find Attribute object
                        attribute_obj = self._converter.convert_attribute(attribute_name=attr['name'])
                        attribute_obj.save()

                        # Create ProductAttribute object
                        self._converter.convert_product_attribute(
                            product=product_obj,
                            attribute=attribute_obj,
                            position=attr['position'],
                        ).save()

                    for v in product.get('variants'):
                        variant_obj = self._converter.convert_variant(variant=v, product=product_obj)
                        variant_obj.save()
                        sizing_objects = self._converter.convert_size_guide(product=product, variant=variant_obj)
                        for sizing_obj in sizing_objects:
                            sizing_obj.save()

        except (IntegrityError, DataError) as error:
            self.logger.exception(error)
        except Exception as error:
            self.logger.exception(error)
