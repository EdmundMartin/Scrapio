from abc import ABC, abstractmethod
from asyncio import Queue
from typing import List


class AbstractProxyManager(ABC):

    @abstractmethod
    async def get_proxy(self) -> str:
        pass


class RoundRobinProxy(AbstractProxyManager):

    def __init__(self, proxies: List[str]):
        self._queue = Queue()
        self.__launch_queue(proxies)

    def __launch_queue(self, proxies: List[str]) -> None:
        for i in proxies:
            self._queue.put_nowait(i)

    async def get_proxy(self) -> str:
        proxy = await self._queue.get()
        await self._queue.put(proxy)
        return proxy