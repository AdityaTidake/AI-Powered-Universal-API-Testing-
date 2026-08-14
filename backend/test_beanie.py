import asyncio
import motor.motor_asyncio
import beanie
from beanie import init_beanie, Document

class User(Document):
    name: str

async def test():
    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
    await init_beanie(database=client.test, document_models=[User])
    print('Beanie works!')

if __name__ == '__main__':
    asyncio.run(test())
