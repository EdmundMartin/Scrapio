from abc import ABC
from typing import Dict


class AbstractRetry(ABC):
    async def should_retry(self, url: str) -> bool:
        ...

    async def on_success(self, url: str) -> None:
        ...


class NoOpRetryStrategy(AbstractRetry):
    async def should_retry(self, url: str) -> bool:
        return False

    async def on_success(self, url: str) -> None:
        return


class SimpleAttempts(AbstractRetry):

    __slots__ = ["retry_counter", "max_retries"]

    def __init__(self, max_retries: int):
        self.retry_counter: Dict[str, int] = {}
        self.max_retries = max_retries

    async def should_retry(self, url: str) -> bool:
        if url not in self.max_retries:
            self.retry_counter[url] = 1
            return 1 < self.max_retries
        self.retry_counter[url] += 1
        return self.retry_counter[url] < self.max_retries

    async def on_success(self, url: str) -> None:
        if url in self.retry_counter:
            del self.retry_counter[url]
