import unittest
import asyncio
from urllib.parse import urlparse

from scrapio.structures.proxies import AbstractProxyManager, RoundRobinProxy
from scrapio.structures.filtering import URLFilter


class TestRoundRobinProxy(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()

    async def proxy_manager_run(self, roundRobin: RoundRobinProxy):
        results = ["Proxy 1", "Proxy 2", "Proxy 3"]
        for i in range(3):
            proxy = await roundRobin.get_proxy()
            self.assertEqual(proxy, results[i])

    def test_is_abstract_method(self):
        self.assertTrue(issubclass(RoundRobinProxy, AbstractProxyManager))

    def test_round_robin_proxy(self):
        rrp = RoundRobinProxy(["Proxy 1", "Proxy 2", "Proxy 3"])
        self.loop.run_until_complete(self.proxy_manager_run(rrp))


class TestURLFiltering(unittest.TestCase):
    def test_can_crawl_crawlable_url(self):
        test_filter = URLFilter(
            [urlparse("http://www.example.com").netloc], None, False
        )
        can_crawl = test_filter.can_crawl(
            "www.example.com", "http://example.com/something/something-else"
        )
        self.assertTrue(can_crawl)

    def test_can_crawl_do_not_crawl(self):
        test_filter = URLFilter(
            [urlparse("http://www.example.com").netloc], None, False
        )
        can_crawl = test_filter.can_crawl("www.no-crawl.com", "http://www.no-crawl.com")
        self.assertFalse(can_crawl)

    def test_can_crawl_crawlable_url_additional_rules(self):
        test_filter = URLFilter(
            [
                urlparse("http://www.example1.com").netloc,
                urlparse("http://www.example2.com").netloc,
            ],
            ["/adult-content", "example2.com/product"],
            False,
        )
        can_crawl = test_filter.can_crawl(
            "www.example1.com", "http://www.example1.com/something-good"
        )
        self.assertTrue(can_crawl)
        can_crawl = test_filter.can_crawl(
            "www.example2.com", "http://www.example2.com/something-good"
        )
        self.assertTrue(can_crawl)

    def test_can_crawl_do_not_crawl_additional_rules(self):
        test_filter = URLFilter(
            [
                urlparse("http://www.example1.com").netloc,
                urlparse("http://www.example2.com").netloc,
            ],
            ["/adult-content", "example2.com/product"],
            False,
        )
        can_crawl = test_filter.can_crawl(
            "www.example1.com", "http://www.example1.com/adult-content"
        )
        self.assertFalse(can_crawl)
        can_crawl = test_filter.can_crawl(
            "www.example2.com", "http://www.example2.com/product-101"
        )
        self.assertFalse(can_crawl)
