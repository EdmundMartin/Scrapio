from concurrent import futures
from collections import defaultdict

#import aiofiles # external dependency
from scrapio.crawlers import BaseCrawler


class OurScraper(BaseCrawler):

    def parse_result(self, response):

        result = defaultdict(lambda: "N/A")
        result['url'] = response._url
        title = response.dom.cssselect('title')
        h1 = response.dom.cssselect('h1')
        if title:
            result['title'] = title[0].text_content()
        if h1:
            result['h1'] = h1[0].text_content()
        return result

    async def save_results(self, result):
        if result:
            """async with aiofiles.open('example_output.csv', 'a') as f:
                url = result.get('url')
                title = result.get('title')
                h1 = result.get('h1')
                await f.write('"{}","{}","{}"\n'.format(url, title, h1))"""
            print(result)


if __name__ == '__main__':
    import time
    pool = futures.ThreadPoolExecutor(max_workers=10)
    crawler = OurScraper('https://www.zoopla.co.uk', max_crawl_size=1000)
    start = time.time()
    crawler.run_scraper(100)
    end = time.time() - start
    print(end)