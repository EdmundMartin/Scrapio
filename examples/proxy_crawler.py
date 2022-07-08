from collections import defaultdict
import logging

from scrapio.crawlers import BaseCrawler
from scrapio.structures.proxies import AbstractProxyManager
from scrapio.utils.helpers import response_to_html
import lxml.html as lh


class OurProxyManager(AbstractProxyManager):

    def __init__(self, **kwargs):
        pass

    async def get_proxy(self):
        return 'http://95.105.90.117:60444'


class OurProxyScraper(BaseCrawler):

    def parse_result(self, response):
        print(response)

    async def save_results(self, result):
        print(result)


if __name__ == '__main__':
    scraper = OurProxyScraper('https://www.zoopla.co.uk', proxy_manager=OurProxyManager, logger_level=logging.INFO)
    scraper.run_crawler(10)