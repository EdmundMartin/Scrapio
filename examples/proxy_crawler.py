from collections import defaultdict

from scrapio.scrapers import BaseScraper
from scrapio.structures.proxies import AbstractProxyManager
from scrapio.utils.helpers import response_to_html
import lxml.html as lh


class OurProxyManager(AbstractProxyManager):

    def __init__(self, **kwargs):
        pass

    async def get_proxy(self):
        return 'http://95.105.90.117:60444'


class OurProxyScraper(BaseScraper):

    def parse_result(self, response):
        html = response_to_html(response)
        dom = lh.fromstring(html)

        result = defaultdict(lambda: "N/A")
        result['url'] = response.url
        title = dom.cssselect('title')
        h1 = dom.cssselect('h1')
        if title:
            result['title'] = title[0].text_content()
        if h1:
            result['h1'] = h1[0].text_content()
        return result

    async def save_results(self, result):
        print(result)


if __name__ == '__main__':
    scraper = OurProxyScraper.create_scraper('https://www.zoopla.co.uk', proxy_manager=OurProxyManager)
    scraper.run_scraper(10, 2)