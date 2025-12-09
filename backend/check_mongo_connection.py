import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys

async def check_mongo():
    print("Attempting to connect to MongoDB...")
    try:
        client = AsyncIOMotorClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
        # Force a connection
        await client.admin.command('ping')
        print("✅ MongoDB is running and accessible!")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(check_mongo())
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"Script error: {e}")
        sys.exit(1)
