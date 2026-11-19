from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    _instance = None
    _client = None
    _db = None

    @classmethod
    def get_database(cls):
        if cls._db is None:
            uri = getattr(settings, 'MONGODB_URI', 'mongodb://localhost:27017/diginote')
            db_name = getattr(settings, 'MONGODB_DB_NAME', 'diginote')
            cls._client = MongoClient(uri)
            cls._db = cls._client.get_default_database() or cls._client[db_name]
            logger.info(f"Connected to MongoDB database: {cls._db.name}")
            cls._ensure_indexes()
        return cls._db

    @classmethod
    def _ensure_indexes(cls):
        """
        Explicitly ensure optimal database indexes matching the interview requirements.
        Zero unnecessary indexes.
        """
        try:
            db = cls._db

            # 1. Users collection indexes
            db.users.create_index([("email", ASCENDING)], unique=True)
            db.users.create_index([("createdAt", DESCENDING)])
            db.users.create_index([("interests", ASCENDING)])

            # 2. Notes collection indexes (Compound for user notes, single for admin notes)
            db.notes.create_index([("userId", ASCENDING), ("createdAt", DESCENDING)])
            db.notes.create_index([("createdAt", DESCENDING)])

            # 3. Posts collection indexes (Compound for lookup join, single for public feed)
            db.posts.create_index([("userId", ASCENDING), ("createdAt", DESCENDING)])
            db.posts.create_index([("createdAt", DESCENDING)])
        except Exception as e:
            logger.warning(f"Could not automatically create MongoDB indexes: {e}")

    @classmethod
    def get_collection(cls, collection_name):
        db = cls.get_database()
        return db[collection_name]


# Convenient shortcuts
def get_db():
    return MongoDB.get_database()

def get_users_col():
    return MongoDB.get_collection('users')

def get_notes_col():
    return MongoDB.get_collection('notes')

def get_posts_col():
    return MongoDB.get_collection('posts')
