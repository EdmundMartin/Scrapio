import asyncio
from typing import Union


class JobQueue(asyncio.Queue):

    __slots__ = ['_seen_urls', '_active_jobs', '_seen_semaphore', '_max_crawl_size', '_page_count']

    def __init__(self, max_crawl_size: Union[int, None]):
        self._seen_urls = set()
        self._active_jobs = 0
        self._seen_semaphore = asyncio.BoundedSemaphore(1)
        self._max_crawl_size = max_crawl_size
        self._page_count = 0
        super().__init__(0)

    async def put_unique_url(self, url):
        async with self._seen_semaphore:
            if url not in self._seen_urls:
                if self._max_crawl_size and self._page_count < self._max_crawl_size:
                    await self.put(('Request', url))
                elif self._max_crawl_size is None:
                    await self.put(('Request', url))
                self._page_count += 1
            self._seen_urls.add(url)

    async def put_parse_request(self, response):
        await self.put(('Parse', response))

    async def get_next_job(self):
        while True:
            try:
                next_job = self.get_nowait()
                self._active_jobs += 1
            except asyncio.QueueEmpty:
                if self._active_jobs > 0:
                    await asyncio.sleep(0.001)
                else:
                    raise asyncio.QueueEmpty("Queue empty with no pending jobs")
            else:
                return next_job

    def completed_task(self):
        self._active_jobs -= 1


class NewJobQueue:

    def __init__(self, max_crawl_size: Union[int, None]):
        self._seen_urls = set()
        self._active_jobs = 0
        self._seen_semaphore = asyncio.BoundedSemaphore(1)
        self._max_crawl_size = max_crawl_size
        self._page_count = 0
        self._request_queue = asyncio.Queue()
        self._parse_queue = asyncio.Queue()

    async def put_unique_url(self, url):
        async with self._seen_semaphore:
            if url not in self._seen_urls:
                if self._max_crawl_size and self._page_count < self._max_crawl_size:
                    await self._request_queue.put(url)
                elif self._max_crawl_size is None:
                    await self._request_queue.put(url)
                self._page_count += 1
            self._seen_urls.add(url)

    async def get_next_url(self):
        while True:
            try:
                next_job = self._request_queue.get_nowait()
                self._active_jobs += 1
            except asyncio.QueueEmpty:
                if self._active_jobs > 0:
                    await asyncio.sleep(0.001)
                else:
                    raise asyncio.QueueEmpty("Queue empty with no pending jobs")
            else:
                return next_job

    async def put_parse_request(self, response):
        await self._parse_queue.put(response)

    async def get_next_parse_job(self):
        while True:
            try:
                next_job = self._parse_queue.get_nowait()
                self._active_jobs += 1
            except asyncio.QueueEmpty:
                if self._active_jobs > 0:
                    await asyncio.sleep(0.001)
                else:
                    raise asyncio.QueueEmpty("Queue empty with no pending jobs")
            else:
                return next_job

    def completed_task(self):
        self._active_jobs -= 1