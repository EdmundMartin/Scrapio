from typing import Union, Dict

from aiohttp import ClientResponse, ClientSession

from scrapio.structures.proxies import AbstractProxyManager


async def get_proxy_from_manager(proxy_manager: Union[AbstractProxyManager, None]) -> Union[str, None]:
    if proxy_manager:
        return await proxy_manager.get_proxy()
    return None


def create_client_session(headers: Union[None, Dict[str, str]], timeout=30) -> ClientSession:
    d_headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
               'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.9',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
    if headers:
        for k, v in headers.items():
            d_headers[k] = v
    return ClientSession(headers=d_headers, conn_timeout=timeout)


def response_to_html(response: ClientResponse) -> str:
    return response._body.decode('utf-8', errors='ignore')
