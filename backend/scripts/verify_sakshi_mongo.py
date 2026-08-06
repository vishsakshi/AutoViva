import pymongo
from app.core.config import settings

def verify_mongo_users():
    client = pymongo.MongoClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]
    users_col = db["users"]

    print("Querying MongoDB users collection for Sakshi...")
    sakshi_users = list(users_col.find({"name": {"$regex": "Sakshi", "$options": "i"}}))
    print(f"Found {len(sakshi_users)} user records for Sakshi in MongoDB:")

    for u in sakshi_users:
        print(f" - ID: {u.get('user_id')}, Name: {u.get('name')}, Email: {u.get('email')}, Role: {u.get('role')}, HashedPassword: {u.get('hashed_password')[:20]}...")

    assert len(sakshi_users) > 0, "No Sakshi user found in MongoDB!"
    print("[VERIFIED]: User 'Sakshi' successfully created & stored in MongoDB!")

if __name__ == "__main__":
    verify_mongo_users()
