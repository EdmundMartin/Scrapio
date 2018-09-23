import unittest
import asyncio

from structures.proxies import AbstractProxyManager, RoundRobinProxy
from structures.queues import URLQueue, TimeoutQueue


class TestRoundRobinProxy(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()

    async def proxy_manager_run(self, roundRobin: RoundRobinProxy):
        results = ['Proxy 1', 'Proxy 2', 'Proxy 3']
        for i in range(3):
            proxy = await roundRobin.get_proxy()
            self.assertEqual(proxy, results[i])

    def test_is_abstract_method(self):
        self.assertTrue(issubclass(RoundRobinProxy, AbstractProxyManager))

    def test_round_robin_proxy(self):
        rrp = RoundRobinProxy(['Proxy 1', 'Proxy 2', 'Proxy 3'])
        self.loop.run_until_complete(self.proxy_manager_run(rrp))


class TestTimeOutQueue(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()

    async def run_timeout_queue(self, timeout):
        timeoutQ = TimeoutQueue()
        res = await timeoutQ.get_max_wait(timeout)

    def test_timeout(self):
        with self.assertRaises(asyncio.TimeoutError):
            self.loop.run_until_complete(self.run_timeout_queue(1))