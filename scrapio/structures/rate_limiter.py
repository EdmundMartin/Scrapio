from abc import ABC, abstractmethod
import asyncio
from typing import Dict
import time
from urllib.parse import urlparse


class AbstractLimiter(ABC):

    @abstractmethod
    async def limited(self, url: str) -> None:
        pass


class RateLimiter(AbstractLimiter):

    def __init__(self, reqs_per_second: int):
        self._rate_limit = reqs_per_second
        self._start_time: time.time = time.time()
        self._url_count: int = 0

    async def limited(self, url: str) -> None:
        elapsed = time.time() - self._start_time
        while self._url_count / elapsed > self._rate_limit:
            await asyncio.sleep(0.01)
            elapsed = time.time() - self._start_time
        self._url_count += 1
        return


class HostLimiter(AbstractLimiter):

    def __init__(self, host_dict: Dict[str, int]):
        self._count_per_domain: Dict[str, int] = {}
        self._hosts, self.host_times = self._load_hosts(host_dict)
        self._start_time: time.time = time.time()

    def _load_hosts(self, host_dict: Dict[str, int]):
        hosts = {}
        host_times = {}
        for k, v in host_dict.items():
            u = urlparse(k).netloc
            hosts[u] = v
            host_times[u] = v
            self._count_per_domain[u] = 0
        return hosts

    async def limited(self, url: str) -> None:
        netloc = urlparse(url).netloc
        if netloc in self._hosts:
            count: int = self._count_per_domain[netloc]
            elapsed = time.time() - self._start_time
            while count / elapsed > self._hosts[netloc]:
                await asyncio.sleep(0.01)
                elapsed = time.time() - self._start_time
            self._count_per_domain[netloc] += 1
            return
        return
