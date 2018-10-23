from scrapio.scrapers import BaseCrawler


class CfCrawler(BaseCrawler):

    async def _create_client_session(self):
        async with self._creation_semaphore:
            try:
                from aiocfscrape import CloudflareScraper
            except ImportError:
                raise ImportError('Cfcrawler requires aiocfscrape')
            self._client = CloudflareScraper()