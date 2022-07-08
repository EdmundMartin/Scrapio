import asyncio
from typing import Union, List
import enum

from scrapio.url_set.set_container import SetContainer
from scrapio.url_set.abstract_set import AbstractUrlSet
from scrapio.url_set.trie_container import TrieContainer


class JobType(enum.Enum):
    Crawl = 1
    Parse = 2


class WorkQueue:

    __slots__ = [
        "_seen_urls",
        "_active_jobs",
        "_seen_semaphore",
        "_max_crawl_size",
        "_page_count",
        "_queue",
    ]

    def __init__(
        self,
        max_crawl_size: Union[int, None],
        seed_urls: Union[List[str], str],
        seen_url_handler: AbstractUrlSet = None,
    ):
        self._seen_urls: AbstractUrlSet = seen_url_handler or TrieContainer()
        self._active_jobs = 0
        self._max_crawl_size = max_crawl_size
        self._page_count = 0
        self._queue = asyncio.Queue()
        self.seed_queue(seed_urls)

    def seed_queue(self, seed_urls: Union[List[str], str]):
        if isinstance(seed_urls, str):
            self._queue.put_nowait(seed_urls)
        elif isinstance(seed_urls, (set, list)):
            for item in seed_urls:
                self._queue.put_nowait(item)

    async def get_job(self) -> str:
        return await self._queue.get()

    async def put_url(self, url):
        if url not in self._seen_urls:
            if self._max_crawl_size and self._page_count < self._max_crawl_size:
                await self._queue.put(url)
            elif self._max_crawl_size is None:
                await self._queue.put(url)
            self._page_count += 1
        self._seen_urls.put(url)

    def task_done(self):
        self._queue.task_done()

    async def join(self):
        return await self._queue.join()
