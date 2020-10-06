import logging
from typing import Union

from aiohttp import ClientSession, ClientResponse, ClientError, ClientTimeout

from scrapio.structures.proxies import AbstractProxyManager
from scrapio.utils.helpers import get_proxy_from_manager


async def get_with_client(client: ClientSession, client_timeout: ClientTimeout, proxy_manager: Union[None, AbstractProxyManager]
                          , url: str) -> ClientResponse:
    proxy = await get_proxy_from_manager(proxy_manager)
    async with client.get(url, timeout=client_timeout, proxy=proxy) as resp:
        try:
            await resp.read()
        except ClientError:
            logger = logging.getLogger('ScrapIO')
            logger.warning('ClientError for URL: {}'.format(url))
        except Exception as e:
            logger = logging.getLogger('ScrapIO')
            logger.warning('Unexpected error for URL: {}'.format(e))
        else:
            return resp
