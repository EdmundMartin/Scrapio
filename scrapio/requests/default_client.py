from typing import Dict, Optional, Union
import logging

from aiohttp import ClientSession, ClientTimeout, ClientError

from scrapio.structures.proxies import AbstractProxyManager
from scrapio.requests.client import AbstractClient
from scrapio.requests.response import from_aiohttp_response
from scrapio.utils.helpers import get_proxy_from_manager


_DEFAULT_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    }


def _get_headers(additional_headers: Optional[Dict[str, str]]):
    if additional_headers and isinstance(additional_headers, dict):
        return {**_DEFAULT_HEADERS, **additional_headers}
    return _DEFAULT_HEADERS


def _build_client_session(timeout: Union[float, int], **kwargs) -> ClientSession:
    aiohttp_timeout_rules = kwargs.get("aiohttp_timeout_rules")
    if aiohttp_timeout_rules and isinstance(aiohttp_timeout_rules, dict):
        aiohttp_timeout = ClientTimeout(**aiohttp_timeout_rules)
        return ClientSession(headers=_get_headers(kwargs.get("headers")), timeout=aiohttp_timeout)
    else:
        return ClientSession(headers=_get_headers(kwargs.get("headers")), conn_timeout=float(timeout))


class DefaultClient(AbstractClient):

    def __init__(self, timeout, **kwargs):
        self.session = _build_client_session(timeout, **kwargs)

    async def get_request(self, url: str, proxy_manager: Optional[AbstractProxyManager]):
        proxy = await get_proxy_from_manager(proxy_manager)
        async with self.session.get(url, proxy=proxy) as resp:
            try:
                await resp.read()
            except ClientError:
                logger = logging.getLogger("ScrapIO")
                logger.warning("ClientError for URL: {}".format(url))
            except Exception as e:
                logger = logging.getLogger("ScrapIO")
                logger.warning("Unexpected error for URL: {}".format(e))
            else:
                return await from_aiohttp_response(resp)

    async def close(self):
        await self.session.close()


