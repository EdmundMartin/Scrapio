# Scrapio
Asyncio web scraping framework. The project aims to make easy to write a highly performant scrapers with little knowledge of asyncio, while giving enough flexibility so that users can customise behaviour of their scrapers.

## Install
```
pip install scrapio
```
The project can be installed using Pip.

## Hello Crawl Example

```python
from collections import defaultdict

import aiofiles # external dependency
import lxml.html as lh
from scrapio.scrapers.base_scraper import BaseScraper
from scrapio.utils.helpers import response_to_html


class OurScraper(BaseScraper):

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
        if result:
            async with aiofiles.open('example_output.csv', 'a') as f:
                url = result.get('url')
                title = result.get('title')
                h1 = result.get('h1')
                await f.write('"{}","{}","{}"\n'.format(url, title, h1))


if __name__ == '__main__':
    scraper = OurScraper.create_scraper('http://edmundmartin.com')
    scraper.run_scraper(10, 2)
```
The above represents a fully functional scraper using the Scrapio framework. We overide the parse_result and save_results from the base scraper class. We then initialize the crawler with our start URL and set the number of scraping processes and the number of parsing processes.

## Custom Link Parsing
The default behaviour of the link parser can be overwriting the behaviour of the base link parsing class as is outlined in the example below.
```python3
from collections import defaultdict

import aiofiles # external dependency
import lxml.html as lh
from scrapio.scrapers import BaseScraper
from scrapio.utils.helpers import response_to_html
from scrapio.structures.filtering import URLFilter


class PythonURLFilter(URLFilter):

    def can_crawl(self, host: str, url: str):
        if 'edmundmartin.com' in host and 'python' in url.lower():
            return True
        return False


class OurScraper(BaseScraper):

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
        if result:
            async with aiofiles.open('example_output.csv', 'a') as f:
                url = result.get('url')
                title = result.get('title')
                h1 = result.get('h1')
                await f.write('"{}","{}","{}"\n'.format(url, title, h1))


if __name__ == '__main__':
    scraper = OurScraper.create_scraper('http://edmundmartin.com', custom_filter=PythonURLFilter)
    scraper.run_scraper(10, 2)
```
