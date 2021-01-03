from typing import Dict, Optional

from aiohttp import ClientResponse


class Response:

    def __init__(self):
        self.url = Optional[str] = None
        self.headers = Optional[Dict] = None
        self.body: Optional[str] = None

    @classmethod
    def from_aiohttp_response(cls, client_response: ClientResponse) -> 'Response':
        resp = cls()
        resp.url = client_response.url
        resp.headers = client_response.headers
        resp.body = client_response.content
        return resp
