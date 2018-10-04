from collections import defaultdict
from lxml import html as lh

from scrapio.mixins.mongo import MongoMixin
from scrapio.scrapers import BaseScraper
from scrapio.utils.helpers import response_to_html


class OurMongoScraper(MongoMixin, BaseScraper):

    def parse_result(self, response):
        html = response_to_html(response)
        dom = lh.fromstring(html)

        result = defaultdict(lambda: "N/A")
        result['url'] = str(response.url)
        title = dom.cssselect('title')
        h1 = dom.cssselect('h1')
        if title:
            result['title'] = title[0].text_content()
        if h1:
            result['h1'] = h1[0].text_content()
        return dict(result)


if __name__ == '__main__':
    crawler = OurMongoScraper.create_scraper('http://edmundmartin.com')
    crawler.create_mongo_client('mongodb://localhost:27017/', 'example', 'crawl')
    crawler.run_scraper(10, 2)