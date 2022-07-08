import unittest
from scrapio.url_set.trie_container import TrieContainerOptimised


class TestTrieContainerOptimised(unittest.TestCase):

    def test_correctly_checks_for_url(self):
        container = TrieContainerOptimised()
        container.put("https://google.com/edmund")
        container.put("https://google.com/edmund/martin")
        container.put("https://john.co.uk/something")

        self.assertTrue("https://google.com/edmund" in container)
        self.assertTrue("https://google.com/edmund/martin" in container)
        self.assertFalse("https://google.com/edmund/martin/something" in container)
        self.assertFalse("https://google.com" in container)
