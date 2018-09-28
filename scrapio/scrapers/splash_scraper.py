import asyncio
from typing import Union
from urllib.parse import urljoin

from scrapio.scrapers.base_scraper import BaseScraper
from scrapio.requests.get import get_with_splash


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


class SplashScraper(BaseScraper):

    def __init__(self, spalsh_configuration: SplashConfiguration, *args, **kwargs):
        self.splash_configuration = spalsh_configuration
        super().__init__(*args, **kwargs)

    async def __consume_request_queue(self, consumer: int):
        self.__remaining_coroutines += 1
        while True:
            try:
                url = await self._request_queue.get_max_wait(30)
                self._logger.info('Thread: {}, Requesting URL: {}'.format(consumer, url))
                splash_location = self.splash_configuration.splash_url.format(url)
                proxy = await self._proxy_manager.get_proxy()
                if proxy:
                    splash_location += '&proxy={}'.format(proxy)
                resp = await get_with_splash(self._client, self._client_timeout, splash_location)
                self._parse_queue.put_nowait(resp)
            except asyncio.TimeoutError:
                self._logger.info('Thread: {}, No more URLs, Consumer shutting down'.format(consumer))
                self.__remaining_coroutines -= 1
                if self.__remaining_coroutines <= 0:
                    await self._client.close()
                return
            except Exception as e:
                self._logger.warning("Thread: {}, Encountered exception: {}".format(consumer, e))