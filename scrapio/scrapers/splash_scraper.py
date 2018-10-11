import asyncio
import logging
from typing import Union, List, Any
from urllib.parse import urljoin

from aiohttp import ClientSession, ClientTimeout, ClientResponse

from scrapio.structures.filtering import URLFilter
from scrapio.parsing.links import link_extractor
from scrapio.structures.queues import JobQueue
from scrapio.requests.get import get_with_splash
from scrapio.structures.proxies import AbstractProxyManager
from scrapio.utils.helpers import create_client_session


__all__ = [
    'SplashConfiguration',
    'SplashScraper',
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


class SplashScraper:

    def __init__(self, spalsh_configuration: SplashConfiguration,  start_url: Union[List[str], str],
                 max_crawl_size=None, **kwargs):
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

        self._task_queue = JobQueue(max_crawl_size=max_crawl_size)

        self._executor = kwargs.get('executor', None)
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        self._logger = kwargs.get('logger', logging.getLogger("Scraper"))

        self.__remaining_coroutines = 0

    def _get_best_event_loop(self):
        try:
            import uvloop
        except ImportError:
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
                self._task_queue.put_nowait(('Request', i))
        elif isinstance(self._start_url, str):
            self._task_queue.put_nowait(('Request', self._start_url))
        return self

    def parse_result(self, response: ClientResponse) -> Any:
        raise NotImplementedError

    async def save_results(self, result):
        raise NotImplementedError

    async def __consume_queue(self, consumer: int):
        self.__remaining_coroutines += 1
        while True:
            try:
                task, item = await self._task_queue.get_next_job()
                if task == 'Request':
                    await self._make_requests(consumer, item)
                else:
                    await self._parse_response(consumer, item)
                self._task_queue.completed_task()
            except asyncio.QueueEmpty:
                self._logger.info('Thread: {}, No more URLs, Consumer shutting down'.format(consumer))
                self.__remaining_coroutines -= 1
                if self.__remaining_coroutines <= 0:
                    await self._client.close()
                return
            except Exception as e:
                self._logger.warning("Thread: {}, Encountered exception: {}".format(consumer, e))
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
            resp._url = url # Splash unfortunately loses the URL redirect information from the request
            self._task_queue.put_nowait(('Parse', resp))
        except Exception as e:
            self._logger.warning("Thread: {}, Encountered exception: {}".format(consumer, e))

    async def _parse_response(self, consumer: int, response: ClientResponse) -> None:
        try:
            loop = asyncio.get_event_loop()
            links = await loop.run_in_executor(self._executor, link_extractor, response, self._url_filter)
            parsed_data = await loop.run_in_executor(self._executor, self.parse_result, response)
            await self.save_results(parsed_data)
            for link in links:
                await self._task_queue.put_unique_url(link)
        except Exception as e:
            self._logger.warning('Parser: {}, Encountered exception: {}'.format(consumer, e))

    def run_scraper(self, workers: int) -> None:
        work_group = asyncio.gather(*[self.__consume_queue(i) for i in range(workers)])

        loop = self._get_best_event_loop()
        try:
            loop.run_until_complete(work_group)
        finally:
            loop.close()
