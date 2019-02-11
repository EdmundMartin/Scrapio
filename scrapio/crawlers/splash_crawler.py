import asyncio
import logging
from typing import Union, List, Any
from urllib.parse import urljoin

from aiohttp import ClientSession, ClientTimeout, ClientResponse

from scrapio.structures.filtering import URLFilter
from scrapio.parsing.links import link_extractor
from scrapio.structures.queues import NewJobQueue
from scrapio.requests.get import get_with_splash
from scrapio.structures.proxies import AbstractProxyManager
from scrapio.utils.helpers import create_client_session


__all__ = [
    'SplashConfiguration',
    'SplashCrawler',
]


class SplashConfiguration:

    def __init__(self, location: str, timeout: int, wait: int, mode: str ='render.html',):
        if mode not in ['render.html']:
            raise TypeError("SplashScraper currently only supports render.html")
        self.splash_url = self._build_splash_url(location, mode, timeout, wait)
        self._render_mode = mode

    @staticmethod
    def _build_splash_url(location, mode, timeout, wait) -> str:
        base_url = urljoin(location, mode)
        url_el = '?url={url}'
        params = '&timeout={timeout}&wait={wait}'.format(timeout=timeout, wait=wait)
        url_el += params
        return '{}{}'.format(base_url, url_el)


class SplashCrawler:

    def __init__(self, spalsh_configuration: SplashConfiguration,  start_url: Union[List[str], str],
                 max_crawl_size: Union[int, None] = None, timeout=30, user_agent=None,  **kwargs):
        self.splash_configuration = spalsh_configuration
        self._start_url = start_url
        self._client: Union[None, ClientSession] = None
        self._client_timeout: Union[None, ClientTimeout] = None
        self._timeout: Union[int, None] = None

        self._proxy_manager: \
            Union[None, AbstractProxyManager] = kwargs.get('proxy_manager')(**kwargs) if kwargs.get(
            'proxy_manager') else None

        custom_filter = kwargs.get('custom_filter')
        if custom_filter and issubclass(custom_filter, URLFilter):
            self._url_filter = custom_filter(start_url, kwargs.get('additional_rules', []), kwargs.get('follow_robots'),
                                             True)
        else:
            self._url_filter = URLFilter(start_url, kwargs.get('additional_rules', []),
                                         kwargs.get('follow_robots', True))

        self._task_queue = NewJobQueue(max_crawl_size=max_crawl_size)

        self._executor = kwargs.get('executor', None)
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        self._logger = kwargs.get('logger', logging.getLogger("Scraper"))
        self.__seed_url_queue(start_url)
        self._timeout = timeout
        self._client_timeout = ClientTimeout(total=float(self._timeout), **kwargs)
        self.__remaining_coroutines = 0
        self.__user_agent = user_agent
        self.__creation_semaphore = asyncio.BoundedSemaphore(1)

    @staticmethod
    def _setup_timeout_rules(timeout: Union[float, int], **kwargs) -> ClientTimeout:
        if kwargs.get('client_timeout_rules') and isinstance('client_timeout_rules', dict):
            rules = kwargs.get('client_timeout_rules')
            return ClientTimeout(**rules)
        return ClientTimeout(total=float(timeout))

    def __seed_url_queue(self, start_url) -> None:
        if isinstance(start_url, str):
            self._task_queue._request_queue.put_nowait(start_url)
        elif isinstance(start_url, (set, list)):
            for item in start_url:
                self._task_queue._request_queue.put_nowait(item)

    async def __create_client_session(self):
        async with self.__creation_semaphore:
            if self._client is None:
                self._client = create_client_session(self.__user_agent)

    def _get_best_event_loop(self):
        try:
            import uvloop
        except ImportError:
            self._logger.info('No UVLoop reverting to base event loop implementation')
            return asyncio.get_event_loop()
        else:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            return asyncio.get_event_loop()

    def parse_result(self, response: ClientResponse) -> Any:
        raise NotImplementedError

    async def save_results(self, result):
        raise NotImplementedError

    async def __consume_request_queue(self, consumer: int):
        await self.__create_client_session()
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

    async def _make_requests(self, consumer: int, url: str):
        try:
            self._logger.info('Thread: {}, Requesting URL: {}'.format(consumer, url))
            splash_location = self.splash_configuration.splash_url.format(url=url)
            if self._proxy_manager:
                proxy = await self._proxy_manager.get_proxy()
                if proxy:
                    splash_location += '&proxy={}'.format(proxy)
            resp = await get_with_splash(self._client, self._client_timeout, splash_location)
            resp._url = url  # Splash unfortunately loses the URL redirect information from the request
            self._task_queue.put_nowait(('Parse', resp))
        except Exception as e:
            self._logger.warning("Thread: {}, Encountered exception: {}".format(consumer, e))

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

    async def _parse_response(self, consumer: int, response: ClientResponse, defrag: bool) -> None:
        try:
            loop = asyncio.get_event_loop()
            html, links = await loop.run_in_executor(self._executor, link_extractor, response, self._url_filter, defrag)
            parsed_data = await loop.run_in_executor(self._executor, self.parse_result, html, response)
            await self.save_results(parsed_data)
            for link in links:
                await self._task_queue.put_unique_url(link)
        except Exception as e:
            self._logger.warning('Parser: {}, Encountered exception: {}'.format(consumer, e))

    def run_scraper(self, workers: int) -> None:
        groups = [self.__consume_parse_queue(i) for i in range(workers)]
        groups += [self.__consume_request_queue(i) for i in range(workers)]
        work_group = asyncio.gather(*groups)

        loop = self._get_best_event_loop()
        try:
            loop.run_until_complete(work_group)
        finally:
            loop.close()
