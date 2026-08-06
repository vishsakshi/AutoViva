import asyncio
import pymongo
from app.core.config import settings

def test_mongo_connection():
    print("Testing MongoDB connection...")
    print(f"URI: {settings.MONGO_URI}")
    print(f"DB Name: {settings.DB_NAME}")

    try:
        client = pymongo.MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("[SUCCESS]: Connected to MongoDB!")
        db = client[settings.DB_NAME]
        print(f"Collections: {db.list_collection_names()}")
        return True
    except Exception as e:
        print(f"[NOTICE]: Local MongoDB standalone ping error ({e}). Will use persistent embedded database store.")
        return False

if __name__ == "__main__":
    test_mongo_connection()
