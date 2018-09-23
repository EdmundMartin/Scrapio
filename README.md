# Scrapio
Asyncio web scraping framework. Work in progress.

## Example

```python
from scrapio.scrapers.base_scraper import BaseScraper


class OurScraper(BaseScraper):

    def parse_result(self, response):
        print('Result')

    async def save_results(self, *args, **kwargs):
        print('Saving')


if __name__ == '__main__':
    scraper = OurScraper.create_scraper('http://www.net-a-porter.com')
    scraper.run_scraper(10, 2)
```
The above outlines how to create a simple scraper using the framework.
Using ten request coroutines and two processing coroutines. Things are likely to break as it's highly experimental and 
untested.