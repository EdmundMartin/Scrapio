from aiohttp import ClientSession, ClientResponse, ClientError


async def get_with_client(client: ClientSession, url: str) -> ClientResponse:
    async with client.get(url) as resp:
        try:
            html = await resp.read()
        except ClientError:
            print('ClientError')
        else:
            print(resp)
            return resp
