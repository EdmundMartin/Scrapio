from collections import defaultdict

import lxml.html as lh

from scrapio.crawlers import SplashConfiguration, SplashCrawler


class ExampleSplashScraper(SplashCrawler):

    def parse_result(self, html, response):
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
    splash_config = SplashConfiguration('http://localhost:8050', 30, 10)
    scraper = ExampleSplashScraper(splash_config, 'http://edmundmartin.com')
    scraper.run_scraper(10)