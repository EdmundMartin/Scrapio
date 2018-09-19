from aiohttp import ClientSession, ClientResponse, ClientError, ClientTimeout


async def get_with_client(client: ClientSession, client_timeout: ClientTimeout, url: str) -> ClientResponse:
    async with client.get(url, timeout=client_timeout) as resp:
        try:
            html = await resp.read()
        except ClientError:
            print('ClientError')
        else:
            print(resp)
            return resp
