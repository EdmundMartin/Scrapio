from urllib.parse import urlparse
from typing import Union, List


def hosts_from_url(raw_urls: Union[List[str], None], start_url: str) -> List[str]:
    if raw_urls is None:
        return [urlparse(start_url).netloc]
    netlocs = []
    for url in raw_urls:
        netlocs.append(urlparse(url).netloc)
    return list(set(netlocs))