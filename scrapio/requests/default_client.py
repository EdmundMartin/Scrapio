from typing import Dict, Optional
import logging

from aiohttp import ClientSession, ClientError

from scrapio.structures.proxies import AbstractProxyManager
from scrapio.requests.client import AbstractClient
from scrapio.requests.response import from_aiohttp_response
from scrapio.utils.helpers import get_proxy_from_manager
from scrapio.requests.client_configuration import TimeoutRules, get_default_timeout


class DefaultClient(AbstractClient):

    __slots__ = (
        "session",
        "headers",
        "timeout_rules"
    )

    def __init__(
        self,
        timeout_rules: Optional[TimeoutRules] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        timeout_rules = (
            timeout_rules._to_aiohttp()
            if timeout_rules
            else get_default_timeout()._to_aiohttp()
        )
        self.session: Optional[ClientSession] = None
        self.headers = headers
        self.timeout_rules = timeout_rules

    async def _get_client(self):
        if self.session:
            return
        self.session = ClientSession(headers=self.headers, timeout=self.timeout_rules)

    async def get_request(
        self, url: str, proxy_manager: Optional[AbstractProxyManager]
    ):
        await self._get_client()
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
