from collections import defaultdict

#import aiofiles # external dependency
import lxml.html as lh
from scrapio.crawlers import BaseCrawler
from scrapio.url_set.trie_container import TrieContainer


class OurScraper(BaseCrawler):

    def parse_result(self, response):
        print(response)

    async def save_results(self, result):
        if result:
            """async with aiofiles.open('example_output.csv', 'a') as f:
                url = result.get('url')
                title = result.get('title')
                h1 = result.get('h1')
                await f.write('"{}","{}","{}"\n'.format(url, title, h1))"""
            print(result)


if __name__ == '__main__':
    scraper = OurScraper('https://www.dailymail.co.uk/home/index.html', verbose=True,
                         seen_url_handler=TrieContainer(),
                         rate_limit=1)
    scraper.run_scraper(10)