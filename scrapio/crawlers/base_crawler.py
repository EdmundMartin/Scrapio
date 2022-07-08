import asyncio
import logging
from typing import Union, List, Any


from aiohttp import ClientTimeout

from scrapio.parsing.links import link_extractor
from scrapio.requests.default_client import DefaultClient
from scrapio.requests.response import Response
from scrapio.structures.queues import WorkQueue
from scrapio.structures.proxies import AbstractProxyManager
from scrapio.structures.rate_limiter import RateLimiter
from scrapio.structures.filtering import URLFilter

__all__ = ["BaseCrawler"]


class BaseCrawler:
    def __init__(
        self,
        start_url: Union[List[str], str],
        max_crawl_size=None,
        timeout=30,
        verbose=True,
        logger_level=logging.WARN,
        **kwargs
    ):
        self._start_url = start_url
        self._client = DefaultClient(timeout, **kwargs)
        self._client_timeout: Union[None, ClientTimeout] = None
        self._timeout: Union[int, None] = None

        self._proxy_manager: Union[None, AbstractProxyManager] = (
            kwargs.get("proxy_manager")(**kwargs)
            if kwargs.get("proxy_manager")
            else None
        )
        self._url_filter = self._set_url_filter(start_url, **kwargs)
        self._queue = WorkQueue(
            max_crawl_size,
            start_url,
            seen_url_handler=kwargs.get("seen_url_handler", None),
        )
        logging.basicConfig(level=logger_level, format="%(message)s")
        self._logger = kwargs.get("logger", logging.getLogger("Scraper"))
        self._client_timeout = self._setup_timeout_rules(timeout)

        self.verbose = verbose
        self._rate_limiter = (
            RateLimiter(kwargs.get("rate_limit")) if kwargs.get("rate_limit") else None
        )

    @staticmethod
    def _set_url_filter(start_url, **kwargs) -> URLFilter:
        custom_filter = kwargs.get("custom_filter")
        if custom_filter and issubclass(custom_filter, URLFilter):
            return custom_filter(
                start_url,
                kwargs.get("additional_rules", []),
                kwargs.get("follow_robots", True),
                kwargs.get("defragment_urls", True),
            )
        return URLFilter(
            start_url,
            kwargs.get("additional_rules", []),
            kwargs.get("follow_robots", True),
            kwargs.get("defragment_urls", True),
        )

    @staticmethod
    def _setup_timeout_rules(timeout: Union[float, int], **kwargs) -> ClientTimeout:
        if kwargs.get("client_timeout_rules") and isinstance(
            "client_timeout_rules", dict
        ):
            rules = kwargs.get("client_timeout_rules")
            return ClientTimeout(**rules)
        return ClientTimeout(total=float(timeout))

    def _get_best_event_loop(self):
        try:
            import uvloop
        except ImportError:
            self._logger.info(
                "Uvloop not found reverting to base event loop implementation"
            )
            return asyncio.get_event_loop()
        else:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            return asyncio.get_event_loop()

    def parse_result(self, response: Response) -> Any:
        raise NotImplementedError

    async def save_results(self, result):
        raise NotImplementedError

    async def _make_requests(self, consumer: int, url: str):
        try:
            self._logger.info("Coroutine: {}, Requesting URL: {}".format(consumer, url))
            if self._rate_limiter:
                await self._rate_limiter.limited(url)
            resp = await self._client.get_request(url, self._proxy_manager)
            await asyncio.sleep(0.001)
            await self._parse_response(consumer, resp)
        except Exception as e:
            self._logger.warning(
                "Coroutine: {}, Encountered exception: {}".format(consumer, e)
            )
            raise e
        finally:
            self._queue.task_done()

    async def _parse_response(self, consumer: int, response: Response) -> None:
        defrag = self._url_filter.defragment
        try:
            response, links = link_extractor(response, self._url_filter, defrag)
            parsed_data = self.parse_result(response)
            await self.save_results(parsed_data)
            for link in links:
                await self._queue.put_url(link)
        except Exception as e:
            self._logger.warning(
                "Coroutine: {}, Encountered exception: {}".format(consumer, e)
            )

    async def _process(self, consumer: int):
        while True:
            try:
                job = await self._queue.get_job()
                await self._make_requests(consumer, job)
            except asyncio.CancelledError:
                return

    async def _crawl(self, workers):
        workers = [asyncio.Task(self._process(i)) for i in range(workers)]
        await self._queue.join()
        for worker in workers:
            worker.cancel()

    async def _close(self):
        await self._client.close()

    def run_crawler(self, workers: int) -> None:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self._crawl(workers))
        except KeyboardInterrupt:
            logging.info("Shutting down - received keyboard interrupt")
        finally:
            loop.run_until_complete(self._close())
            loop.close()
