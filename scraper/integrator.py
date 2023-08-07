import logging
from django.db import transaction, IntegrityError, DataError

from scraper import constants, scrapers, parsers, converters


class DataIntegrator:
    def __init__(self, scraper: scrapers.ShopifyScraper, parser: parsers.ShopifyParser,
                 converter: converters.DataConverter):
        self._scraper = scraper
        self._parser = parser
        self._converter = converter
        self._parsed_product = []
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
        self._parsed_product = self._parser.read_parsed_file_data()

    def scrape_save(self):
        scraped_products = self._scraper.fetch_products()
        self._scraper.save_products(scraped_products)

    def parse_save(self):
        scraped_products = self._scraper.read_scraped_file_data()
        self._parsed_product = self._parser.parse_products(scraped_products)
        self._parser.save_products(self._parsed_product)

    def integrate(self):
        objects_count = {'Products': 0, 'Product Categories': 0, 'Variants': 0, 'Product Attributes': 0, 'Sizings': 0}

        try:
            with transaction.atomic():
                shop_obj = self._converter.shop
                shop_obj.save()

                for product in self._parsed_product:
                    product_obj = self._converter.convert_product(product=product, shop=shop_obj)
                    product_obj.save()
                    objects_count['Products'] += 1

                    categories = self._converter.convert_categories(product)
                    product_obj.categories.set(categories)
                    objects_count['Product Categories'] += len(categories)

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
                        objects_count['Product Attributes'] += 1

                    for v in product.get('variants'):
                        variant_obj = self._converter.convert_variant(variant=v, product=product_obj)
                        variant_obj.save()
                        objects_count['Variants'] += 1

                        sizing_objects = self._converter.convert_sizings(product=product, variant=variant_obj)
                        for sizing_obj in sizing_objects:
                            sizing_obj.save()
                            objects_count['Sizings'] += 1

                print(objects_count)
        except (IntegrityError, DataError) as error:
            self.logger.exception(error)
        except Exception as error:
            self.logger.exception(error)
