from urllib.parse import urlparse
from typing import List

from scrapio.url_set.abstract_set import AbstractUrlSet


class TrieContainer(AbstractUrlSet):

    __slots__ = (
        'trie',
        '_end_symbol'
    )

    def __init__(self):
        self.trie = dict()
        self._end_symbol = "END"

    def make_parts(self, url: str) -> List[str]:
        parsed = urlparse(url)
        parts = [parsed.scheme, parsed.netloc]
        for item in parsed.path.split('/'):
            parts.append(item)
        return parts

    def __contains__(self, item):
        sub_trie = self.trie
        parts = self.make_parts(item)
        for char in parts:
            if char in sub_trie:
                sub_trie = sub_trie[char]
            else:
                return False
        else:
            if self._end_symbol in sub_trie:
                return True
            else:
                return False

    def put(self, url: str) -> None:
        if url in self:
            return
        temp_trie = self.trie
        parts = self.make_parts(url)
        for char in parts:
            if char in temp_trie:
                temp_trie = temp_trie[char]
            else:
                temp_trie = temp_trie.setdefault(char, {})
        temp_trie[self._end_symbol] = self._end_symbol
