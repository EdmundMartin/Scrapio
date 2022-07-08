from typing import Dict, Optional, Any

from aiohttp import ClientResponse


class Response:

    __slots__ = [
        'url',
        'status',
        'headers',
        'body',
        'raw_response'
    ]

    def __init__(self):
        self.url: Optional[str] = None
        self.status: Optional[int] = None
        self.headers: Optional[Dict] = None
        self.body: Optional[str] = None
        self.raw_response: Optional[Any] = None

    def __repr__(self):
        return f"<Response: {self.url} {self.status}>"


async def from_aiohttp_response(client_response: ClientResponse) -> Response:
    resp = Response()
    resp.url = client_response.url
    resp.status = client_response.status
    resp.headers = client_response.headers
    bytes = await client_response.read()
    resp.body = bytes.decode("utf-8", errors='ignore')
    resp.raw_response = client_response
    return resp
