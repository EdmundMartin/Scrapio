import asyncio
import logging
from typing import Union, List, Any


from aiohttp import ClientSession, ClientResponse, ClientTimeout

from scrapio.parsing.links import link_extractor
from scrapio.requests.get import get_with_client
from scrapio.structures.queues import TimeoutQueue, URLQueue
from scrapio.structures.proxies import AbstractProxyManager
from scrapio.structures.filtering import URLFilter
from scrapio.utils.helpers import create_client_session


__all__ = [
    'BaseScraper'
]


class BaseScraper:

    def __init__(self, start_url: Union[List[str], str], max_crawl_size=None, **kwargs):
        self._start_url = start_url
        self._client: Union[None, ClientSession] = None
        self._client_timeout: Union[None, ClientTimeout] = None
        self._timeout: Union[int, None] = None

        self._queue_timeout = kwargs.get('queue_timeout', 30)
        self._proxy_manager: \
            Union[None, AbstractProxyManager] = kwargs.get('proxy_manager')(**kwargs) if kwargs.get('proxy_manager') else None

        custom_filter = kwargs.get('custom_filter')
        if custom_filter and issubclass(custom_filter, URLFilter):
            self._url_filter = custom_filter(start_url, kwargs.get('additional_rules', []), kwargs.get('follow_robots'), True)
        else:
            self._url_filter = URLFilter(start_url, kwargs.get('additional_rules', []), kwargs.get('follow_robots', True))

        self._request_queue = URLQueue(max_crawl_size)
        self._parse_queue = TimeoutQueue()

        self._executor = kwargs.get('executor', None)
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        self._logger = kwargs.get('logger', logging.getLogger("Scraper"))

        self.__remaining_coroutines = 0

    def _get_best_event_loop(self):
        try:
            import uvloop
        except ImportError as e:
            self._logger.info('No UVLoop reverting to base event loop implementation')
            return asyncio.get_event_loop()
        else:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            return asyncio.get_event_loop()

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

    async def save_results(self, result):
        raise NotImplementedError

    async def __consume_request_queue(self, consumer: int):
        self.__remaining_coroutines += 1
        while True:
            try:
                url = await self._request_queue.get_max_wait(self._queue_timeout)
                self._logger.info('Thread: {}, Requesting URL: {}'.format(consumer, url))
                resp = await get_with_client(self._client, self._client_timeout, self._proxy_manager, url)
                self._parse_queue.put_nowait(resp)
            except asyncio.TimeoutError:
                self._logger.info('Thread: {}, No more URLs, Consumer shutting down'.format(consumer))
                self.__remaining_coroutines -= 1
                if self.__remaining_coroutines <= 0:
                    await self._client.close()
                return
            except Exception as e:
                self._logger.warning("Thread: {}, Encountered exception: {}".format(consumer, e))

    async def __consume_parse_queue(self, consumer: int) -> None:
        while True:
            try:
                loop = asyncio.get_event_loop()
                resp = await self._parse_queue.get_max_wait(self._queue_timeout)
                links = await loop.run_in_executor(self._executor, link_extractor, resp, self._url_filter)
                parsed_data = await loop.run_in_executor(self._executor, self.parse_result, resp)
                await self.save_results(parsed_data)
                for link in links:
                    await self._request_queue.put_unique_url(link)
            except asyncio.TimeoutError:
                self._logger.info('Parser: {}, Message: No more Responses, consumer shutting down'.format(consumer))
                return
            except Exception as e:
                self._logger.warning('Parser: {}, Encountered exception: {}'.format(consumer, e))

    def run_scraper(self, request_workers: int, parse_workers: int) -> None:
        request_group = asyncio.gather(*[self.__consume_request_queue(i) for i in range(request_workers)])
        parser_group = asyncio.gather(*[self.__consume_parse_queue(i) for i in range(parse_workers)])

        loop = self._get_best_event_loop()
        try:
            all_groups = asyncio.gather(request_group, parser_group)
            loop.run_until_complete(all_groups)
        finally:
            loop.close()

