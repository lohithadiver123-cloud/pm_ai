"""
MongoDB database connection using Motor async driver.
Provides a shared client instance and database reference.
Falls back to JSON-based database if MongoDB is unavailable.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


# Create a single Motor client instance for the application
client: AsyncIOMotorClient = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)

# Reference to the pm_copilot database
db = client[settings.DB_NAME]

# Flag to track if MongoDB is available
_mongodb_available = False


async def get_database() -> AsyncIOMotorClient:
    """Return the database instance for use in dependency injection."""
    return db


async def connect_to_mongo() -> None:
    """Verify MongoDB connection is alive. Call on app startup."""
    global _mongodb_available
    try:
        # Use a short timeout for the ping command
        await asyncio.wait_for(
            client.admin.command('ping'),
            timeout=5.0
        )
        print("Successfully connected to MongoDB.")
        _mongodb_available = True
    except asyncio.TimeoutError:
        print("MongoDB connection timeout - using fallback JSON database")
        print("Check your MongoDB Atlas connection string and network")
        _mongodb_available = False
    except Exception as e:
        # Log the error but don't crash - collections will be created on first use
        print(f"MongoDB connection warning: {type(e).__name__}")
        print("Using fallback JSON database for Milestone 1 demo...")
        _mongodb_available = False


async def close_mongo_connection() -> None:
    """Close the MongoDB client connection. Call on app shutdown."""
    if _mongodb_available:
        client.close()
        print("MongoDB connection closed.")
