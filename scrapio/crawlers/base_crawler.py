import asyncio
import logging
from typing import Union, List, Any


from aiohttp import ClientSession, ClientResponse, ClientTimeout

from scrapio.parsing.links import link_extractor
from scrapio.requests.get import get_with_client
from scrapio.structures.queues import NewJobQueue
from scrapio.structures.proxies import AbstractProxyManager
from scrapio.structures.rate_limiter import RateLimiter
from scrapio.structures.filtering import URLFilter
from scrapio.utils.helpers import create_client_session


__all__ = [
    'BaseCrawler'
]


class BaseCrawler:

    def __init__(self, start_url: Union[List[str], str], max_crawl_size=None, timeout=30, user_agent=None,
                 verbose=True, **kwargs):
        self._start_url = start_url
        self._client: Union[None, ClientSession] = None
        self._client_timeout: Union[None, ClientTimeout] = None
        self._timeout: Union[int, None] = None

        self._proxy_manager: \
            Union[None, AbstractProxyManager] = kwargs.get('proxy_manager')(**kwargs) if kwargs.get('proxy_manager') else None
        self._url_filter = self._set_url_filter(start_url, **kwargs)
        self._task_queue = NewJobQueue(max_crawl_size, start_url)

        self._executor = kwargs.get('executor', None)
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        self._logger = kwargs.get('logger', logging.getLogger("Scraper"))
        self._client_timeout = self._setup_timeout_rules(timeout)

        self.verbose = verbose
        self._rate_limiter = RateLimiter(kwargs.get('rate_limit')) if kwargs.get('rate_limit') else None
        self.__remaining_coroutines = 0
        self.__user_agent = user_agent
        self._creation_semaphore = asyncio.BoundedSemaphore(1)

    @staticmethod
    def _set_url_filter(start_url, **kwargs) -> URLFilter:
        custom_filter = kwargs.get('custom_filter')
        if custom_filter and issubclass(custom_filter, URLFilter):
            return custom_filter(start_url, kwargs.get('additional_rules', []), kwargs.get('follow_robots', True),
                                 kwargs.get('defragment_urls', True))
        return URLFilter(start_url, kwargs.get('additional_rules', []), kwargs.get('follow_robots', True),
                         kwargs.get('defragment_urls', True))

    @staticmethod
    def _setup_timeout_rules(timeout: Union[float, int], **kwargs) -> ClientTimeout:
        if kwargs.get('client_timeout_rules') and isinstance('client_timeout_rules', dict):
            rules = kwargs.get('client_timeout_rules')
            return ClientTimeout(**rules)
        return ClientTimeout(total=float(timeout))

    async def _create_client_session(self) -> None:
        async with self._creation_semaphore:
            if self._client is None:
                self._client = create_client_session(self.__user_agent)

    def _get_best_event_loop(self):
        try:
            import uvloop
        except ImportError:
            self._logger.info('Uvloop not found reverting to base event loop implementation')
            return asyncio.get_event_loop()
        else:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            return asyncio.get_event_loop()

    def parse_result(self, response: ClientResponse) -> Any:
        raise NotImplementedError

    async def save_results(self, result):
        raise NotImplementedError

    async def __consume_request_queue(self, consumer: int):
        await self._create_client_session()
        self.__remaining_coroutines += 1

        while True:
            try:
                item = await self._task_queue.get_next_url()
                await self._make_requests(consumer, item)
                self._task_queue.completed_task()
            except asyncio.QueueEmpty:
                self._logger.info('Coroutine: {}, No more URLs, Consumer shutting down'.format(consumer))
                self.__remaining_coroutines -= 1
                if self.__remaining_coroutines <= 0:
                    await self._client.close()
                return
            except Exception as e:
                self._logger.warning("Coroutine: {}, Encountered exception: {}".format(consumer, e))
                self._task_queue.completed_task()

    async def __consume_parse_queue(self, consumer: int):
        defrag = self._url_filter.defragment
        while True:
            try:
                item = await self._task_queue.get_next_parse_job()
                await self._parse_response(consumer, item, defrag)
                self._task_queue.completed_task()
            except asyncio.QueueEmpty:
                return
            except Exception as e:
                self._logger.warning("Coroutine: {}, Encountered exception: {}".format(consumer, e))
                self._task_queue.completed_task()

    async def _make_requests(self, consumer: int, url: str):
        try:
            if self.verbose:
                self._logger.info('Coroutine: {}, Requesting URL: {}'.format(consumer, url))
            if self._rate_limiter:
                await self._rate_limiter.limited(url)
            resp = await get_with_client(self._client, self._client_timeout, self._proxy_manager, url)
            await self._task_queue.put_parse_request(resp)
        except Exception as e:
            self._logger.warning("Coroutine: {}, Encountered exception: {}".format(consumer, e))

    async def _parse_response(self, consumer: int, response: ClientResponse, defrag: bool) -> None:
        try:
            loop = asyncio.get_event_loop()
            response, links = await loop.run_in_executor(self._executor, link_extractor, response, self._url_filter, defrag)
            parsed_data = await loop.run_in_executor(self._executor, self.parse_result, response)
            await self.save_results(parsed_data)
            for link in links:
                await self._task_queue.put_unique_url(link)
        except Exception as e:
            self._logger.warning('Coroutine: {}, Encountered exception: {}'.format(consumer, e))

    def run_scraper(self, workers: int) -> None:
        groups = [self.__consume_parse_queue(i) for i in range(workers)]
        groups += [self.__consume_request_queue(i) for i in range(workers)]
        work_group = asyncio.gather(*groups)

        loop = self._get_best_event_loop()
        try:
            loop.run_until_complete(work_group)
        finally:
            loop.close()

