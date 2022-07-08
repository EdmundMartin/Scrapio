from typing import List
from urllib.parse import urlparse, urljoin, urldefrag

from scrapio.requests.response import Response
import lxml.html as lh

from scrapio.structures.filtering import URLFilter


def link_extractor(
    response: Response, url_filter: URLFilter, defrag: bool
) -> (str, List[str]):
    html = response.body
    req_url = response.url
    dom = lh.fromstring(html)
    found_urls = []
    for href in dom.xpath("//a/@href"):
        url = urljoin(str(req_url), href)
        if defrag:
            url = urldefrag(url)[0]
        netloc = urlparse(url).netloc
        can_crawl = url_filter.can_crawl(netloc, url)
        if can_crawl:
            found_urls.append(url)
    return response, found_urls
