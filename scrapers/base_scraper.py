import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging
from typing import Union, List, Any


from aiohttp import ClientSession, ClientResponse, ClientTimeout

from parsing.links import link_extractor
from requests.get import get_with_client
from structures.queues import TimeoutQueue, URLQueue
from structures.filtering import URLFilter
from utils.helpers import create_client_session
from utils.urls import hosts_from_url


class BaseScraper:

    def __init__(self, start_url: Union[List[str], str], max_crawl_size=None, **kwargs):
        self._start_url = start_url
        self._client: Union[None, ClientSession] = None
        self._client_timeout: Union[None, ClientTimeout] = None
        self._timeout: Union[int, None] = None

        self._url_filter = URLFilter(start_url, kwargs.get('additional_rules', []), kwargs.get('follow_robots', True))

        self._request_queue = URLQueue(max_crawl_size)
        self._parse_queue = TimeoutQueue()

        self._executor = kwargs.get('executor', None)
        self._logger = kwargs.get('logger', logging.getLogger("Scraper"))

        self.__remaining_coroutines = 0

    @classmethod
    def create_scraper(cls, *args, timeout=30, user_agent=None, **kwargs):
        self = cls(*args, **kwargs)
        self._client = create_client_session(user_agent)
        self._timeout = timeout
        if kwargs.get('client_timeout_rules') and isinstance('client_timeout_rules', dict):
            rules = kwargs.get('client_timeout_rules')
            self._client_timeout = ClientTimeout(**rules)
        else:
            self._client_timeout = ClientTimeout(total=float(self._timeout))
        if isinstance(self._start_url, list):
            for i in self._start_url:
                self._request_queue.put_nowait(i)
        elif isinstance(self._start_url, str):
            self._request_queue.put_nowait(self._start_url)
        return self

    def parse_result(self, response: ClientResponse) -> Any:
        raise NotImplementedError

    async def save_results(self, *args, **kwargs):
        raise NotImplementedError

    async def consume_request_queue(self):
        self.__remaining_coroutines += 1
        while True:
            try:
                url = await self._request_queue.get_max_wait(30)
                print(url)
                self._logger.info('Requesting URL: {}'.format(url))
                resp = await get_with_client(self._client, self._client_timeout, url)
                self._parse_queue.put_nowait(resp)
            except asyncio.TimeoutError:
                print('Run out of URLs')
                self.__remaining_coroutines -= 1
                if self.__remaining_coroutines <= 0:
                    await self._client.close()
                return

    async def consume_parse_queue(self) -> None:
        while True:
            try:
                loop = asyncio.get_event_loop()
                resp = await self._parse_queue.get_max_wait(30)
                links = await loop.run_in_executor(self._executor, link_extractor, resp, self._url_filter, True)
                parsed_data = await loop.run_in_executor(self._executor, self.parse_result, resp)
                await self.save_results(parsed_data)
                for link in links:
                    await self._request_queue.put_unique_url(link)
            except asyncio.TimeoutError:
                print('Run out of parse responses')
                return

    def run_scraper(self, request_workers: int, parse_workers: int) -> None:
        request_group = asyncio.gather(*[self.consume_request_queue() for i in range(request_workers)])
        parser_group = asyncio.gather(*[self.consume_parse_queue() for i in range(parse_workers)])

        loop = asyncio.get_event_loop()
        try:
            all_groups = asyncio.gather(request_group, parser_group)
            loop.run_until_complete(all_groups)
        finally:
            loop.close()

