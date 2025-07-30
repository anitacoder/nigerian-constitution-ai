from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConstitutionDb:
    def __init__(self, mongo_url: str, db_name: str):
        self.mongo_url = mongo_url
        self.db_name = db_name
        
        self.collections = {
            'documents': 'documents',
        }
        self.client = None
        self.db = None
        
        self.connect()

    def connect(self, max_retries=5, retry_delay=5):
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to MongoDB at: {self.mongo_url}")
                
                self.client = MongoClient(
                    self.mongo_url,
                    serverSelectionTimeoutMS=10000, 
                    socketTimeoutMS=10000,
                    connectTimeoutMS=10000,
                )
                
                self.client.admin.command('ping')
                self.db = self.client[self.db_name]
                logger.info(f"Successfully connected to {self.db_name} database")
                return True
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.warning(f"MongoDB connection attempt {attempt + 1} failed: {e}")
                self.client = None 
                self.db = None 
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Could not connect to MongoDB.")
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error during MongoDB connection: {e}")
                self.client = None 
                self.db = None 
                return False

    def get_collection(self, collection_name: str):
        if self.db is None:
            if not self.connect():
                logger.error("No database connection")
                return None
        if self.db is None:
            logger.error("Database object is still None after connection attempts. Cannot get collection.")
            return None
                
        collection = self.db[collection_name]
        logger.info(f"Retrieved collection: {collection_name}")
        return collection

    def close_connection(self):
        if self.client:
            self.client.close()
            logger.info("Database connection closed.")
            self.client = None
            self.db = None