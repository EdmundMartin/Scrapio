from collections import defaultdict

import aiofiles # external dependency
import lxml.html as lh
from scrapio.crawlers import BaseCrawler
from scrapio.utils.helpers import response_to_html
from scrapio.structures.filtering import URLFilter


class PythonURLFilter(URLFilter):

    def can_crawl(self, host: str, url: str):
        if 'edmundmartin.com' in host and 'python' in url.lower():
            return True
        return False


class OurScraper(BaseCrawler):

    def parse_result(self, response):
        return response

    async def save_results(self, result):
        if result:
            async with aiofiles.open('example_output.csv', 'a') as f:
                url = result.get('url')
                title = result.get('title')
                h1 = result.get('h1')
                await f.write('"{}","{}","{}"\n'.format(url, title, h1))


if __name__ == '__main__':
    scraper = OurScraper('http://edmundmartin.com', custom_filter=PythonURLFilter)
    scraper.run_crawler(10)