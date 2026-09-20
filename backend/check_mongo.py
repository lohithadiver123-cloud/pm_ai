import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import json
import os

async def main():
    print(f"MONGO_URI: {settings.MONGO_URI[:25]}...")
    print(f"DB_NAME: {settings.DB_NAME}")
    
    # 1. Check fallback JSON DB
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    print(f"Data dir exists: {os.path.exists(data_dir)}")
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            path = os.path.join(data_dir, f)
            print(f"  Fallback file {f}: {os.path.getsize(path)} bytes")
            if "user" in f:
                with open(path, "r", encoding="utf-8") as fp:
                    users_data = json.load(fp)
                    print(f"  Fallback users: {[u.get('email') for u in users_data]}")

    # 2. Check MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[settings.DB_NAME]
    try:
        await client.admin.command('ping')
        print("MongoDB Atlas: PING SUCCESSFUL!")
        collections = await db.list_collection_names()
        print(f"Collections in {settings.DB_NAME}: {collections}")
        for c in collections:
            cnt = await db[c].count_documents({})
            print(f"  - {c}: {cnt} documents")
        
        users = await db.users.find({}).to_list(100)
        print(f"\nTotal users in MongoDB Atlas ({len(users)}):")
        for u in users:
            print(f"  User ID: {u.get('_id')}")
            print(f"  Email: {u.get('email')}")
            print(f"  Name: {u.get('name')}")
            pw_hash = u.get('password_hash', '')
            print(f"  Hash format: {pw_hash[:25]}... (length={len(pw_hash)})")
    except Exception as e:
        print("MongoDB Atlas Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
