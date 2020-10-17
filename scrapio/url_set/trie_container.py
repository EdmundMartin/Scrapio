from scrapio.url_set.abstract_set import AbstractUrlSet


class TrieContainer(AbstractUrlSet):
    def __init__(self):
        self._trie = dict()
        self._end_symbol = "END"

    def __contains__(self, item):
        sub_trie = self._trie

        for char in item:
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

        temp_trie = self._trie
        for char in url:
            if char in temp_trie:
                temp_trie = temp_trie[char]
            else:
                temp_trie = temp_trie.setdefault(char, {})
        temp_trie[self._end_symbol] = self._end_symbol
