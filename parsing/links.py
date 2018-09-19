from typing import List
from urllib.parse import urlparse, urljoin, urldefrag

from aiohttp import ClientResponse
import lxml.html as lh


def link_extractor(response: ClientResponse, allowed_domains: List[str], defrag: bool) -> List[str]:
    html = response._body.decode('utf-8', errors='ignore')
    req_url = response.url
    dom = lh.fromstring(html)
    found_urls = []
    for href in dom.xpath('//a/@href'):
        url = urljoin(str(req_url), href)
        netloc = urlparse(url).netloc
        if netloc in allowed_domains:
            found_urls.append(url)
    return found_urls
