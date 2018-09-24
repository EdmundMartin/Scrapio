# Scrapio
Asyncio web scraping framework. The project aims to make easy to write a highly performant scrapers with little knowledge of asyncio, while giving enough flexibility so that users can customise behaviour of their scrapers.

## Install
```
pip install scrapio
```
The project can be installed using Pip.

## Example

```python
from scrapio.scrapers.base_scraper import BaseScraper


class OurScraper(BaseScraper):

    def parse_result(self, response):
        print('Result')

    async def save_results(self, *args, **kwargs):
        print('Saving')


if __name__ == '__main__':
    scraper = OurScraper.create_scraper('http://edmundmartin.com')
    scraper.run_scraper(10, 2)
```
The above outlines how to create a simple scraper using the framework.
Using ten request coroutines and two processing coroutines. Things are likely to break as it's highly experimental and 
untested.
