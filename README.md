# Scrapio
Asyncio web scraping framework. Work in progress.

## Example

```python
from scrapers.base_scraper import BaseScraper


class OurScraper(BaseScraper):

    def parse_result(self, response):
        print('Result')

    async def save_results(self, *args, **kwargs):
        print('Saving')


if __name__ == '__main__':
    scraper = OurScraper.create_scraper('https://www.zoopla.co.uk/')
    scraper.run_scraper(10, 2)
```
The above outlines how to create a simple scraper using the framework.
Using ten request coroutines and two processing coroutines. Things are likely to break as it's highly experimental and 
untested.