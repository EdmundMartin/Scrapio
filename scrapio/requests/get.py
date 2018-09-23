import logging

from aiohttp import ClientSession, ClientResponse, ClientError, ClientTimeout


async def get_with_client(client: ClientSession, client_timeout: ClientTimeout, url: str) -> ClientResponse:
    async with client.get(url, timeout=client_timeout) as resp:
        try:
            html = await resp.read()
        except ClientError:
            logger = logging.getLogger('ScrapIO')
            logger.warning('ClientError for URL: {}'.format(url))
        except Exception as e:
            logger = logging.getLogger('ScrapIO')
            logger.warning('Unexpected error for URL: {}'.format(e))
        else:
            return resp
