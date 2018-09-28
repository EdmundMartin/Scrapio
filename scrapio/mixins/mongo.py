from collections import Iterable
import logging

try:
    import motor.motor_asyncio as motor_async
except ImportError:
    ImportError("motor is required to use MongoMixin")


class MongoMixin:

    def create_mongo_client(self, connection_string: str, database: str, collection: str) -> None:
        client = motor_async.AsyncIOMotorClient(connection_string)
        database = client[database]
        self.__setattr__('mongo_connection', database[collection])

    async def save_results(self, result):
        connection = self.__getattribute__('mongo_connection')
        if isinstance(result, Iterable):
            try:
                await connection.insert_many(result)
            except Exception as e:
                logger = logging.getLogger('Scraper')
                logger.warning('Exception inserting documents into collection: {}'.format(e))
        try:
            await connection.insert(result)
        except Exception as e:
            logger = logging.getLogger('Scraper')
            logger.warning('Exception inserting document into collection: {}'.format(e))