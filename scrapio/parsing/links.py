from typing import List
from urllib.parse import urlparse, urljoin, urldefrag

from aiohttp import ClientResponse
import lxml.html as lh

from scrapio.structures.filtering import AbstractURLFilter, URLFilter
from scrapio.parsing.valid_url import valid_url


def link_extractor(response: ClientResponse, url_filter: URLFilter, defrag: bool) -> (str, List[str]):
    html = response._body.decode('utf-8', errors='ignore')
    req_url = response._url
    dom = lh.fromstring(html)
    response.__setattr__('dom', dom)
    response.__setattr__('html', html)
    found_urls = []
    for href in dom.xpath('//a/@href'):
        url = urljoin(str(req_url), href)
        if defrag:
            url = urldefrag(url)[0]
        netloc = urlparse(url).netloc
        can_crawl = url_filter.can_crawl(netloc, url)
        if can_crawl and valid_url(url):
            found_urls.append(url)
    return response, found_urls
