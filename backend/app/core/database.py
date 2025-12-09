from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        self.client = AsyncIOMotorClient(
            settings.MONGO_URL,
            minPoolSize=1,
            maxPoolSize=10
        )
        self.db = self.client[settings.DB_NAME]
        print(f"Connected to MongoDB: {settings.DB_NAME}")

    def close(self):
        if self.client:
            self.client.close()

# Global database instance
db_instance = Database()

def get_db():
    return db_instance.db
