from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    client = None
    database = None

def get_database():
    if Database.client is None:
        try:
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/inventory_db")
            Database.client = MongoClient(mongodb_url)
            # Test connection
            Database.client.admin.command('ping')
            Database.database = Database.client.get_database()
            logger.info("Connected to MongoDB successfully")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e
    return Database.database

def close_database():
    if Database.client:
        Database.client.close()
        Database.client = None
        Database.database = None

# Collections
def get_products_collection():
    db = get_database()
    return db.products

def get_orders_collection():
    db = get_database()
    return db.orders

def get_users_collection():
    db = get_database()
    return db.users