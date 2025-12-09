import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "edifyminds_db")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key_here")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

settings = Settings()
