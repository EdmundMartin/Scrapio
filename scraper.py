import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging
from typing import Union, List, Any


from aiohttp import ClientSession, ClientResponse

from parsing.links import link_extractor
from requests.get import get_with_client
from structures.queues import TimeoutQueue, URLQueue, EmptyURLQueue
from utils.helpers import create_client_session
from utils.urls import hosts_from_url


class BaseScraper:

    def __init__(self, start_url: Union[List[str], str], allowed_domains=None, max_crawl_size=None, **kwargs):
        self._start_url = start_url
        self._client: Union[None, ClientSession] = None
        self._timeout: Union[int, None] = None
        self._allowed_domains = hosts_from_url(allowed_domains, start_url)

        self._process_pool = ProcessPoolExecutor(max_workers=2)
        self._request_queue = URLQueue(max_crawl_size)
        self._parse_queue = TimeoutQueue()

        self._executor = kwargs.get('executor', None)
        self._logger = kwargs.get('logger', logging.getLogger("Scraper"))

    @classmethod
    async def create_scraper(cls, *args, timeout=30, user_agent=None, **kwargs):
        self = cls(*args, **kwargs)
        self._client = await create_client_session(user_agent)
        self._timeout = timeout
        if isinstance(self._start_url, list):
            for i in self._start_url:
                await self._request_queue.put_unique_url(i)
        elif isinstance(self._start_url, str):
            await self._request_queue.put_unique_url(self._start_url)
        return self

    def parse_result(self, response: ClientResponse) -> Any:
        raise NotImplementedError

    async def save_results(self, *args, **kwargs):
        raise NotImplementedError

    async def consume_request_queue(self):
        while True:
            try:
                url = await self._request_queue.get_max_wait(30)
                self._logger.info('Requesting URL: {}'.format(url))
                resp = await get_with_client(self._client, url)
                self._parse_queue.put_nowait(resp)
            except asyncio.TimeoutError:
                print('Run out of URLs')
                return

    async def consume_parse_queue(self) -> None:
        while True:
            try:
                loop = asyncio.get_event_loop()
                resp = await self._parse_queue.get_max_wait(30)
                links = await loop.run_in_executor(self._executor, link_extractor, resp, self._allowed_domains, True)
                parsed_data = await loop.run_in_executor(self._executor, self.parse_result, resp)
                await self.save_results(parsed_data)
                for link in links:
                    await self._request_queue.put_unique_url(link)
            except asyncio.TimeoutError:
                print('Run out of parse responses')
                return

    async def run_scraper(self, request_workers: int, parse_workers: int) -> None:
        request_group = asyncio.gather(*[self.consume_request_queue() for i in range(request_workers)])
        parser_group = asyncio.gather(*[self.consume_parse_queue() for i in range(parse_workers)])

        loop = asyncio.get_event_loop()
        try:
            all_groups = asyncio.gather(request_group, parser_group)
            loop.run_until_complete(all_groups)
        finally:
            await self._client.close()
            loop.close()


async def run_scraper():
    scraper = await BaseScraper.create_scraper('http://edmundmartin.com')
    await scraper.consume_request_queue()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_scraper())
    loop.close()
