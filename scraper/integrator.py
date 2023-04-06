import json
import logging
from django.db import transaction, IntegrityError, DataError

from scraper import constants
from scraper.scrapers import ShopifyScraper, KitAndAceScraper
from scraper.converter import DataConverter, KitAndAceDataConverter


class DataIntegrator:
    def __init__(self, scraper: ShopifyScraper, converter: DataConverter, parsed_products: list = None):
        self._scraper = scraper
        self._converter = converter
        self._parsed_products = [] if parsed_products is None else parsed_products
        self.logger = logging.getLogger(__name__)

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

                for product in self._parsed_products:
                    product_obj = self._converter.convert_product(product=product, shop=shop_obj)

                    for v in product.get('variants'):
                        variant_obj = self._converter.convert_variant(variant=v, product=product_obj)
                        for attr_key, attr_value in v.get('attributes').items():
                            self._converter.convert_attribute(name=attr_key, value=attr_value, variant=variant_obj)
        except (IntegrityError, DataError) as error:
            self.logger.exception(error)


if __name__ == '__main__':
    # TODO create a log file if not exists (file and dir)
    handler = logging.FileHandler(constants.LOGS_FILE_PATH.format(module_name='integrators'))
    formatter = logging.Formatter(
        fmt=f"%(asctime)s %(module)s %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

    integrator = DataIntegrator(scraper=KitAndAceScraper(), converter=KitAndAceDataConverter())
    # integrator.scrape()
    integrator.load_parsed_products()
    integrator.integrate()
