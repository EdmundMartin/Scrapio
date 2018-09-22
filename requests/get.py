from aiohttp import ClientSession, ClientResponse, ClientError, ClientTimeout, InvalidURL


async def get_with_client(client: ClientSession, client_timeout: ClientTimeout, url: str) -> ClientResponse:
    async with client.get(url, timeout=client_timeout) as resp:
        try:
            html = await resp.read()
        except ClientError:
            print('ClientError')
        except InvalidURL as e:
            print(e)
        except Exception as e:
            print(e)
        else:
            return resp
