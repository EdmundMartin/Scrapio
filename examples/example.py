from scrapio.scrapers.base_scraper import BaseScraper


class OurScraper(BaseScraper):

    def parse_result(self, response):
        print('Result')

    async def save_results(self, *args, **kwargs):
        print('Saving')


if __name__ == '__main__':
    scraper = OurScraper.create_scraper('http://www.net-a-porter.com')
    scraper.run_scraper(10, 2)