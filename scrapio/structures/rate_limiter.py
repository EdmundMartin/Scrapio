import time


class RateLimiter:

    def __init__(self, reqs_per_second: int):
        self._rate_limit = reqs_per_second
        self._start_time: time.time = time.time()
        self._url_count: int = 0

    async def limited(self) -> None:
        elapsed = time.time() - self._start_time
        while self._url_count / elapsed > self._rate_limit:
            await asyncio.sleep(0.01)
            elapsed = time.time() - self._start_time
        self._url_count += 1
        return


if __name__ == '__main__':
    r = RateLimiter(10)
    r._url_count = 100
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(r.limited())
    loop.close()