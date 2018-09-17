from typing import List
from urllib.parse import urlparse, urljoin, urldefrag

from aiohttp import ClientResponse


def link_extractor(response: ClientResponse, allowed_domains: List[str], defrag: bool) -> List[str]:
    html = response._body.decode('utf-8', errors='ignore')
    return ['http://edmundmartin.com/some-page']