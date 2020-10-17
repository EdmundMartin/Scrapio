from abc import abstractmethod, ABC


class AbstractUrlSet(ABC):
    @abstractmethod
    def put(self, url: str) -> None:
        ...

    @abstractmethod
    def __contains__(self, item):
        ...
