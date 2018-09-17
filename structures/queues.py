import asyncio
from typing import Union

from async_timeout import timeout


class EmptyURLQueue(asyncio.QueueEmpty):
    pass


class TimeoutQueue(asyncio.Queue):

    async def get_max_wait(self, wait_time):
        try:
            async with timeout(wait_time):
                return await self.get()
        except TimeoutError:
            raise asyncio.QueueEmpty("Queue Timeout")


class URLQueue(asyncio.Queue):
    
    def __init__(self, max_crawl_size: Union[int, None]):
        self._seen_urls = set()
        self._seen_semaphore = asyncio.BoundedSemaphore(1)
        self._max_crawl_size = max_crawl_size
        self._page_count = 0
        super().__init__(0)

    async def put_unique_url(self, url):
        async with self._seen_semaphore:
            if url not in self._seen_urls:
                if self._max_crawl_size and self._page_count < self._max_crawl_size + 1:
                    await self.put(url)
                elif self._max_crawl_size is None:
                    await self.put(url)
            self._seen_urls.add(url)

    async def get_max_wait(self, wait_time):
        try:
            async with timeout(wait_time):
                return await self.get()
        except TimeoutError:
            raise asyncio.QueueEmpty("Queue Timeout")