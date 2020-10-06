from abc import ABC, abstractmethod
import logging
from typing import List, Union, Dict
from urllib.robotparser import RobotFileParser


class AbstractURLFilter(ABC):

    @abstractmethod
    def can_crawl(self, host: str, url: str) -> bool:
        pass


class URLFilter(AbstractURLFilter):

    __slots__ = ('_net_locations', '_additional_rules', '_robots', '_robots_cache', 'defragment')

    def __init__(self, net_locations: List[str], additional_rules: Union[List[str], None], follow_robots: bool,
                 defragment: bool = True):
        self._net_locations = net_locations
        self._additional_rules = additional_rules
        self._robots = follow_robots
        self._robots_cache = self._gather_robots_files() if follow_robots else None
        self.defragment = defragment

    def _gather_robots_files(self) -> Dict[str, RobotFileParser]:
        robot_cache = dict()
        if isinstance(self._net_locations, list):
            net_locations = self._net_locations
        else:
            net_locations = [self._net_locations]
        for host in net_locations:
            try:
                parser = RobotFileParser(url='http://{}/robots.txt'.format(host))
                parser.read()
                robot_cache[host] = parser
            except Exception:
                logger = logging.getLogger('ScrapIO')
                logger.warning('Was unable to successfully download robots.txt, for: {}'.format(host))
        return robot_cache

    def can_crawl(self, host: str, url: str) -> bool:
        if self._additional_rules:
            value = any(i in url for i in self._additional_rules)
            if value is True:
                return False
        if self._robots:
            robots_rules = self._robots_cache.get(host)
            if robots_rules is None and host in self._net_locations:
                return True
            if robots_rules:
                return robots_rules.can_fetch('*', url) and host in self._net_locations
        return host in self._net_locations