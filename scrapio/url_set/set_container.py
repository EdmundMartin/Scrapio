from scrapio.url_set.abstract_set import AbstractUrlSet


class SetContainer(AbstractUrlSet):

    __slots__ = [
        '_seen'
    ]

    def __init__(self):
        self._seen = set()

    def put(self, url: str):
        self._seen.add(url)

    def __contains__(self, item):
        return item in self._seen
