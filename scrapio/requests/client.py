from abc import ABCMeta, abstractmethod
from typing import Optional

from scrapio.structures.proxies import AbstractProxyManager


class AbstractClient(metaclass=ABCMeta):

    @abstractmethod
    async def get_request(self, url: str, proxy_manager: Optional[AbstractProxyManager]):
        ...
